#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 自恢复（自含外层口令 K2；仅依赖 Python stdlib + openssl CLI，token 零回显）

执行: python3 .ai-vault/restore.py
链路: K2 → 解 vault.key.enc → vault.key → 解 token.enc → token（仅内存）
      → fp16 比对 meta.json → 回写 L1(0600)+L2(0600)+L3(三片,0600)
"""
import base64, hashlib, json, os, subprocess, sys
from pathlib import Path

K2 = "67929cc8ffa66dad3c0879f03c9b8fa55b5a0a6b0aee61bc31957eab9aa2e2ce"
HERE = Path(__file__).resolve().parent              # .ai-vault/
REPO = HERE.parent                                  # snap2edit 仓根
HOME = Path(os.environ.get("TOKENCTL_HOME", REPO.parent))
L1 = Path.home() / ".git-credentials"
L2_VAULT = HOME / ".secrets" / "vault"
L2_KEYS = HOME / ".secrets" / "keys"
L3_DIR = HOME / ".secrets" / "shards"
META = HERE / "meta.json"
OWNER = "dongf9527"
HOST = "github.com"
ITER = 200000


def op_ssl(data, passwd, dec=False):
    cmd = ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", str(ITER)]
    cmd += ["-d"] if dec else ["-salt"]
    cmd += ["-pass", "env:TK_PV"]
    env = dict(os.environ, TK_PV=passwd)
    return subprocess.run(cmd, input=data, capture_output=True, check=True, env=env).stdout


def secure_write(p, data, mode=0o600):
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        data = data.encode()
    with open(p, "wb") as f:
        os.fchmod(f.fileno(), mode)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.chmod(p, mode)


def write_l1(tok):
    r = subprocess.run(["git", "config", "--global", "credential.helper"],
                       capture_output=True, text=True)
    if r.stdout.strip() != "store":
        subprocess.run(["git", "config", "--global", "credential.helper", "store"], check=True)
    lines = []
    if L1.exists():
        lines = [l for l in L1.read_text().splitlines() if "@" + HOST not in l]
    lines.append("https://%s:%s@%s" % (OWNER, tok, HOST))
    L1.write_text("\n".join(lines) + "\n")
    os.chmod(L1, 0o600)


def write_l3(tok):
    n = len(tok)
    a, b = tok[: n // 2], tok[n // 2:]
    L = max(len(a), len(b))
    m = bytes(x ^ y for x, y in zip(a.rjust(L, b"\x00"), b.rjust(L, b"\x00")))
    for i, s in ((1, m), (2, a), (3, b)):
        secure_write(L3_DIR / ("token.shard.%d.b64" % i), base64.b64encode(s))


def main():
    key = op_ssl((HERE / "vault.key.enc").read_bytes(), K2, dec=True).decode()
    tok = op_ssl((HERE / "token.enc").read_bytes(), key, dec=True)
    meta = json.loads(META.read_text())
    fp = hashlib.sha256(tok).hexdigest()[:16]
    if fp != meta["fp16"]:
        print("[restore] 指纹不符（疑似串票）——拒绝落层", file=sys.stderr)
        sys.exit(2)
    # L2: token.enc 用 L0 在库密文原样回写（与 vault.key 同源同配），vault.key 回写明文层
    secure_write(L2_VAULT / "token.enc", (HERE / "token.enc").read_bytes())
    secure_write(L2_KEYS / "vault.key", key)
    write_l1(tok.decode())
    write_l3(tok)
    print("[restore] 本地三层已重建: L1(helper)+L2(token.enc %dB)+L3(3 shards)" % (HERE / "token.enc").stat().st_size)
    print("[restore] mask=%s fp16=%s —— token 零回显" % (meta["mask"], fp))


if __name__ == "__main__":
    main()
