#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tokenctl —— snap2edit 四层 PAT 保管与恢复工具（正本随仓旅行，路径自举）

层位（v2 公开仓适配，详见 docs/TOKEN_MANAGEMENT.md）:
  L0 入仓登记层  <repo>/.ai-vault/   meta.json + README.md（零密文——2026-11-07 事件后，
                                     公开仓不放任何可复原材料，密文链已移出）
  L1 推送热路径  ~/.git-credentials   git credential store 工作文件（0600，唯一明文例外）
  L2 主密文层    <repo>/.secrets/{vault/token.enc, keys/vault.key}（0600，gitignore 隔离）
  L3 三分片兜底  <repo>/.secrets/shards/token.shard.{1,2,3}.b64（0600，任二片重组）

命令: status / verify / wire / ingest --file F / vault-sync / rebuild-shards / push
安全约定: token 明文零 argv、零回显、零落文档；输出仅掩码与 fp16 指纹。
算法: AES-256-CBC + PBKDF2-HMAC-SHA256 20 万迭代（openssl CLI）；
      口令经 env 注入进程，不经 argv、不经终端。
恢复链: L1 缺 → wire（L2→L3 逐层拉回）；L2+L3 俱灭 → owner 重发票（ingest）。
      公开仓不承载密文，无 L0 密文自恢复——吊销+重发是终极兜底。
"""
import base64
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path
from urllib import request as urlreq
from urllib.error import HTTPError
from urllib.parse import urlparse

# ---------- 路径自举 ----------
HERE = Path(__file__).resolve().parent            # <repo>/scripts/
REPO = HERE.parent                                # snap2edit 仓根
# v2 适配：敏感层默认收进本仓 gitignore 隔离区（.secrets/），不再写外层目录
# （事件复盘：v1 默认 REPO.parent 是外层自动化工作区，曾把 L2/L3 写入其 git 跟踪面）
HOME = Path(os.environ.get("TOKENCTL_HOME", REPO))
L0 = REPO / ".ai-vault"
L2_VAULT = HOME / ".secrets" / "vault"
L2_KEYS = HOME / ".secrets" / "keys"
L3_DIR = HOME / ".secrets" / "shards"
L1 = Path.home() / ".git-credentials"
META = L0 / "meta.json"
OWNER = "dongf9527"
HOST = "github.com"
ITER = 200000
PAT_RE = re.compile(r"^(?:ghp_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})$")


# ---------- 基础工具 ----------
def fp16(tok: bytes) -> str:
    return hashlib.sha256(tok).hexdigest()[:16]


def mask_of(tok: bytes) -> str:
    s = tok.decode()
    return s[:11] + "****" + s[-4:] if s.startswith("github_pat_") else s[:4] + "****" + s[-4:]


def op_ssl(data: bytes, passwd: str, dec: bool = False) -> bytes:
    """AES-256-CBC(+PBKDF2 20w) 加解密；数据走 stdin/stdout 管道，口令走 env，零 argv。"""
    cmd = ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", str(ITER)]
    cmd += ["-d"] if dec else ["-salt"]
    cmd += ["-pass", "env:TK_PV"]
    env = dict(os.environ, TK_PV=passwd)
    r = subprocess.run(cmd, input=data, capture_output=True, check=True, env=env)
    return r.stdout


def secure_write(p: Path, data, mode=0o600):
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        data = data.encode()
    with open(p, "wb") as f:
        os.fchmod(f.fileno(), mode)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.chmod(p, mode)


def shred(p: Path):
    """覆写后删除（粉碎原件）。"""
    try:
        sz = p.stat().st_size
        with open(p, "r+b") as f:
            f.write(secrets.token_bytes(sz))
            f.flush()
            os.fsync(f.fileno())
    except OSError:
        pass
    p.unlink(missing_ok=True)


def ensure_helper():
    r = subprocess.run(["git", "config", "--global", "credential.helper"],
                       capture_output=True, text=True)
    if r.stdout.strip() != "store":
        subprocess.run(["git", "config", "--global", "credential.helper", "store"], check=True)


def write_l1(tok: str):
    ensure_helper()
    lines = []
    if L1.exists():
        lines = [l for l in L1.read_text().splitlines() if "@" + HOST not in l]
    lines.append(f"https://{OWNER}:{tok}@{HOST}")
    L1.write_text("\n".join(lines) + "\n")
    os.chmod(L1, 0o600)


def read_l1():
    if not L1.exists():
        return None
    for l in L1.read_text().splitlines():
        if "@" + HOST in l:
            u = urlparse(l if "://" in l else "https://" + l)
            if u.password:
                return u.password
    return None


def read_key():
    k = L2_KEYS / "vault.key"
    return k.read_text().strip() if k.exists() else None


def write_l2(tok: bytes, key: str):
    """token.enc（AES-256-CBC，口令=vault.key）+ vault.key（32B 随机 hex，密钥分离）。"""
    secure_write(L2_VAULT / "token.enc", op_ssl(tok, key))
    secure_write(L2_KEYS / "vault.key", key)


def read_token_l2():
    key = read_key()
    enc = L2_VAULT / "token.enc"
    if not key or not enc.exists():
        return None
    return op_ssl(enc.read_bytes(), key, dec=True)


def make_shards(tok: bytes):
    """token 切半 A‖B；三片 = {1: mask(A⊕B, 短半左零对齐), 2: A, 3: B}。任取两片可重组。"""
    n = len(tok)
    a, b = tok[: n // 2], tok[n // 2:]
    L = max(len(a), len(b))
    m = bytes(x ^ y for x, y in zip(a.rjust(L, b"\x00"), b.rjust(L, b"\x00")))
    return m, a, b


def write_l3(tok: bytes):
    m, a, b = make_shards(tok)
    for i, s in ((1, m), (2, a), (3, b)):
        secure_write(L3_DIR / f"token.shard.{i}.b64", base64.b64encode(s))


def read_shards():
    out = {}
    for i in (1, 2, 3):
        p = L3_DIR / f"token.shard.{i}.b64"
        out[i] = base64.b64decode(p.read_bytes()) if p.exists() else None
    return out


def combine(sh) -> bytes:
    m, a, b = sh.get(1), sh.get(2), sh.get(3)
    if a is not None and b is not None:
        return a + b
    L = len(m) if m else 0
    if m is not None and a is not None:
        return a + bytes(x ^ y for x, y in zip(m, a.rjust(L, b"\x00")))
    if m is not None and b is not None:
        return bytes(x ^ y for x, y in zip(m, b.rjust(L, b"\x00"))).lstrip(b"\x00") + b
    raise RuntimeError("L3 分片不足（需任意两片）")


def load_meta():
    return json.loads(META.read_text()) if META.exists() else None


def save_meta(tok: bytes, login: str, expires=None, expires_note=None):
    meta = load_meta() or {}
    meta.update(mask=mask_of(tok), fp16=fp16(tok), login=login, expires=expires,
                expires_note=expires_note, scheme="https",
                updated=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    secure_write(META, json.dumps(meta, ensure_ascii=False, indent=2) + "\n", mode=0o644)
    return meta


def check_fp(tok: bytes, quiet=False):
    meta = load_meta()
    if meta and "fp16" in meta:
        cur = fp16(tok)
        if cur != meta["fp16"]:
            raise RuntimeError(f"指纹不符（本地 fp16={cur}，在册 {meta['fp16']}）——疑似串票")
        if not quiet:
            print(f"[fp] 指纹与在册一致: fp16={cur}")


def api_verify(tok: bytes):
    req = urlreq.Request("https://api.github.com/user", headers={
        "Authorization": "Bearer " + tok.decode(),
        "User-Agent": "tokenctl-snap2edit",
        "Accept": "application/vnd.github+json",
    })
    try:
        with urlreq.urlopen(req, timeout=25) as r:
            return r.status, json.load(r).get("login")
    except HTTPError as e:
        return e.code, None


def token_from_any_layer():
    """只读取票（不写层）：L1 → L2 → L3 → L0。"""
    t = read_l1()
    if t:
        return t.encode(), "L1"
    t = read_token_l2()
    if t:
        return t, "L2"
    sh = read_shards()
    if sum(1 for v in sh.values() if v) >= 2:
        return combine(sh), "L3"
    return None, None


# ---------- L0（v2 公开仓适配）----------
# v1 的 RESTORE_TEMPLATE（自含外层口令 K2 的自恢复脚本）已随 2026-11-07 安全事件移除：
# public 仓中「密文 + 密钥密文 + 内嵌口令」三件套等同明文公开（复盘见
# docs/TOKEN_MANAGEMENT.md §八）。恢复链改为 L2→L3 本地自愈 + 吊销重发兜底。


# ---------- 七个命令 ----------
def cmd_status():
    m, a, b = read_shards().values()
    n3 = sum(1 for v in (m, a, b) if v is not None)
    l0_ok = META.exists() and (L0 / "README.md").exists()
    l1_ok = L1.exists() and ("@" + HOST) in L1.read_text()
    l1_perm = oct(L1.stat().st_mode & 0o777)[2:] if L1.exists() else "-"
    l2_ok = (L2_VAULT / "token.enc").exists() and (L2_KEYS / "vault.key").exists()
    print(f"[status] L0 {'OK(入仓登记簿)' if l0_ok else '缺失'} / "
          f"L1 {'OK(%s)' % l1_perm if l1_ok else '缺失'} / "
          f"L2 {'OK' if l2_ok else '缺失'} / L3 {n3}/3")
    meta = load_meta()
    if meta:
        print(f"[status] 在册: mask={meta.get('mask')} fp16={meta.get('fp16')} "
              f"login={meta.get('login')} expires={meta.get('expires')} updated={meta.get('updated')}")
    t = read_l1()
    if t:
        fp = fp16(t.encode())
        same = "与在册一致" if meta and fp == meta.get("fp16") else ("与在册不符(疑似串票)" if meta else "无在册记录")
        print(f"[status] 本轮指纹(L1): fp16={fp} —— {same}")


def cmd_verify():
    tok, src = token_from_any_layer()
    if not tok:
        print("[verify] 四层均无可用票——先跑 wire", file=sys.stderr)
        sys.exit(1)
    code, login = api_verify(tok)
    fp = fp16(tok)
    meta = load_meta()
    same = meta and fp == meta.get("fp16")
    if code == 200:
        print(f"[verify] HTTP {code} login={login} fp16={fp}（源={src}）—— 验真通过"
              + ("（与在册指纹一致）" if same else "（无在册记录或不一致）"))
        check_fp(tok)
    else:
        print(f"[verify] HTTP {code} —— 票过期/被吊销或权限不足，走换发 SOP（docs/TOKEN_MANAGEMENT.md §6）",
              file=sys.stderr)
        sys.exit(1)


def cmd_wire():
    # 灾情报告
    m, a, b = read_shards().values()
    n3 = sum(1 for v in (m, a, b) if v is not None)
    l2_ok = (L2_VAULT / "token.enc").exists() and (L2_KEYS / "vault.key").exists()
    print(f"[wire] 灾情: L1 {'缺失' if not read_l1() else '在'} / L2 {'缺失' if not l2_ok else '在'} / "
          f"L3 {n3}/3 / L0 {'OK' if META.exists() else '缺失'}")
    if l2_ok:
        tok = read_token_l2()
        check_fp(tok, quiet=True)
        write_l1(tok.decode())
        write_l3(tok)
        print(f"[restore] 源层=L2 → 本地三层已重建: L1(helper)+L2(token.enc "
              f"{(L2_VAULT / 'token.enc').stat().st_size}B)+L3(3 shards)")
        print(f"[restore] mask={mask_of(tok)} fp16={fp16(tok)} —— token 零回显")
        return
    if n3 >= 2:
        tok = combine(read_shards())
        check_fp(tok, quiet=True)
        key = secrets.token_bytes(32).hex()
        write_l2(tok, key)          # vault.key 已灭 → 新钥重封
        write_l1(tok.decode())
        write_l3(tok)
        cmd_vault_sync()            # L0 登记簿同步（零密文，仅刷新 meta/README）
        print(f"[restore] 源层=L3 → 本地三层已重建（vault.key 轮换，L0 已同步）")
        print(f"[restore] mask={mask_of(tok)} fp16={fp16(tok)} —— token 零回显")
        return
    print("[wire] L2/L3 俱灭，公开仓无密文可拉（v2 设计）——请 owner 后台重发票，"
          "走 ingest（docs/TOKEN_MANAGEMENT.md §六）", file=sys.stderr)
    sys.exit(1)


def cmd_ingest(file: Path, expires=None, expires_note=None):
    raw = file.read_text().strip()
    if not PAT_RE.match(raw):
        print("[ingest] 拒收: 文件首形态不像 PAT（ghp_/github_pat_ 前缀+20 位以上字母数字）", file=sys.stderr)
        sys.exit(1)
    tok = raw.encode()
    code, login = api_verify(tok)
    if code != 200:
        print(f"[ingest] 拒收: GitHub API 验真未过（HTTP {code}）", file=sys.stderr)
        sys.exit(1)
    key = secrets.token_bytes(32).hex()      # 每次 ingest 换新内层密钥
    write_l2(tok, key)
    write_l3(tok)
    write_l1(raw)
    meta = save_meta(tok, login or OWNER, expires=expires, expires_note=expires_note)
    shred(file)
    print(f"[ingest] 三层落位: L2(token.enc {(L2_VAULT / 'token.enc').stat().st_size}B + vault.key 32B-hex) "
          f"+ L3(3 shards) + L1(0600); login={meta['login']}")
    print(f"[ingest] 原件已粉碎; mask={meta['mask']} fp16={meta['fp16']}")
    print("[ingest] 提醒: 请跑 vault-sync 刷新 L0 登记簿（换票后必须，保持户口本与实票一致）")


def cmd_vault_sync():
    """刷新 L0 登记簿（v2 公开仓适配：零密文入仓，只写 meta.json + README.md）。"""
    tok, src = token_from_any_layer()
    if not tok:
        print("[vault-sync] 无可用票源（L1/L2/L3 皆空）——先 wire 或 ingest", file=sys.stderr)
        sys.exit(1)
    meta = load_meta() or {}
    meta.update(mask=mask_of(tok), fp16=fp16(tok), login=meta.get("login", OWNER),
                expires=meta.get("expires"), expires_note=meta.get("expires_note"),
                scheme="https", updated=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                layers={"L0": ".ai-vault/ 登记簿（零密文，公开仓不放可复原材料）",
                        "L1": "~/.git-credentials（0600，唯一明文例外）",
                        "L2": ".secrets/{vault/token.enc, keys/vault.key}（0600，gitignore 隔离）",
                        "L3": ".secrets/shards/token.shard.{1,2,3}.b64（0600，任二片重组）"})
    L0.mkdir(parents=True, exist_ok=True)
    secure_write(META, json.dumps(meta, ensure_ascii=False, indent=2) + "\n", mode=0o644)
    secure_write(L0 / "README.md", L0_README, mode=0o644)
    print(f"[vault-sync] L0 登记簿已刷新（零密文）: meta.json + README.md（票源={src} fp16={fp16(tok)}）")
    print("[vault-sync] 提醒: .ai-vault/ 变更随本轮 commit+push 入 GitHub")


L0_README = """# .ai-vault —— snap2edit 入仓登记层（L0，v2 公开仓适配）

> 2026-11-07 安全事件后重评（docs/TOKEN_MANAGEMENT.md §八）：本仓为 **public**，
> 公开仓不放任何可复原材料——v1 的 `token.enc + vault.key.enc + restore.py(K2 内嵌)`
> 密文链已整体移除（历史提交中的旧密文在旧票吊销后即惰性）。本目录现在只放**登记簿**：

| 文件 | 内容 |
|---|---|
| `meta.json` | token 户口本：mask/fp16/login/expires/updated/layers（SHA-256 前 16 位指纹，不可逆推） |
| `README.md` | 本说明 |

本地敏感层（gitignore 隔离，永不入 git）：

| 层 | 位置 | 说明 |
|---|---|---|
| L1 | `~/.git-credentials` | 推送热路径，0600，唯一明文例外 |
| L2 | `.secrets/{vault/token.enc, keys/vault.key}` | AES-256-CBC + PBKDF2 20 万迭代，密钥分文件，0600 |
| L3 | `.secrets/shards/token.shard.{1,2,3}.b64` | 切半 A‖B + mask=A⊕B，任二片重组，0600 |

灾后恢复：`python3 scripts/tokenctl.py status` → `wire`（L2→L3 逐层拉回）→ `verify`。
L2/L3 俱灭（沙箱整卷清空）→ owner 后台重发票走 `ingest`（吊销+重发是终极兜底）。
详见 `docs/TOKEN_MANAGEMENT.md`。
"""


def cmd_rebuild_shards():
    tok = read_token_l2()
    if not tok:
        print("[rebuild-shards] L2 不全——rebuild 以 L2 为源", file=sys.stderr)
        sys.exit(1)
    check_fp(tok, quiet=True)
    write_l3(tok)
    print("[rebuild-shards] L3 三片已按 L2 重切（确定性切分，fp16 一致）")


def cmd_push(args):
    """git push 包装：输出强制脱敏（token 形态串 → [REDACTED]）。"""
    r = subprocess.run(["git", "push", *args], cwd=REPO, capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    out = re.sub(r"(ghp_|github_pat_)[A-Za-z0-9_]+", lambda m: m.group(1) + "[REDACTED]", out)
    sys.stdout.write(out)
    sys.exit(r.returncode)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    c = sys.argv[1]
    if c == "status":
        cmd_status()
    elif c == "verify":
        cmd_verify()
    elif c == "wire":
        cmd_wire()
    elif c == "ingest":
        i = sys.argv.index("--file") if "--file" in sys.argv else -1
        if i < 0 or i + 1 >= len(sys.argv):
            print("用法: tokenctl.py ingest --file <新票.txt> [--expires YYYY-MM-DD] [--expires-note ...]",
                  file=sys.stderr)
            sys.exit(2)
        f = Path(sys.argv[i + 1])
        kw = {}
        if "--expires" in sys.argv:
            kw["expires"] = sys.argv[sys.argv.index("--expires") + 1]
        if "--expires-note" in sys.argv:
            kw["expires_note"] = sys.argv[sys.argv.index("--expires-note") + 1]
        cmd_ingest(f, **kw)
    elif c == "vault-sync":
        cmd_vault_sync()
    elif c == "rebuild-shards":
        cmd_rebuild_shards()
    elif c == "push":
        cmd_push(sys.argv[2:])
    else:
        print(f"未知命令: {c}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
