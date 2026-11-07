# .ai-vault —— CASE: snap2edit 入仓永续层（L0）

本目录只放**密文与自恢复脚本**（0644 入仓无妨，守卫钩子不拦密文形态）：

| 文件 | 内容 |
|---|---|
| `token.enc` | PAT 密文（AES-256-CBC + PBKDF2-HMAC-SHA256 20 万迭代；口令 = vault.key） |
| `vault.key.enc` | 内层密钥 vault.key 的密文（口令 = K2，K2 内嵌于 restore.py） |
| `restore.py` | 自含 K2 的自恢复脚本（仅依赖 stdlib + openssl CLI）：`python3 .ai-vault/restore.py` |
| `meta.json` | token 户口本（mask/fp16/login/expires/scheme/updated），零 token 材料 |
| `README.md` | 本说明 |

灾后恢复：clone 本仓 → `python3 .ai-vault/restore.py`（或 `python3 scripts/tokenctl.py wire`）→ `verify`。
详见 `docs/TOKEN_MANAGEMENT.md`。
