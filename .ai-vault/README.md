# .ai-vault —— snap2edit 入仓登记层（L0，v2 公开仓适配）

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
