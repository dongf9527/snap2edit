#!/bin/bash
# install_token_guards.sh —— snap2edit PAT 守卫（幂等，可重装）
# 职责:
#   1. 装本仓 pre-commit 钩子: 暂存 diff 中出现 PAT 明文形态串（ghp_/github_pat_ 前缀
#      +20 位以上字母数字）即拒绝提交；掩码形态（github_pat_****XXXX）与 .ai-vault/
#      密文不在拦截面。
#   2. 追加 snap2edit/.gitignore 隔离条目（.secrets/ *.token upload/ .credentials/ 等，
#      双保险: 本地敏感层本就在仓库外，防未来误移入/symlink）。
#   3. 确保 credential.helper=store（L1 热路径前置）。
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK="$REPO/.git/hooks/pre-commit"

mkdir -p "$REPO/.git/hooks"
cat > "$HOOK" <<'HOOK_EOF'
#!/bin/bash
# pre-commit token guard —— 拦截 PAT 明文形态（掩码形态与 .ai-vault 密文不拦）
if git diff --cached -U0 | grep -qE '(ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{60,})'; then
  echo "[token-guard] 检测到 PAT 明文形态，拒绝提交。" >&2
  echo "[token-guard] 若为旧票引述: 确认该票已在 GitHub 后台吊销后改掩码形态（github_pat_****XXXX）。" >&2
  exit 1
fi
exit 0
HOOK_EOF
chmod +x "$HOOK"

# .gitignore 隔离面（幂等追加）
IG="$REPO/.gitignore"
touch "$IG"
for pat in ".secrets/" ".credentials/" "upload/" "*.token" "*.pem" "inbox/"; do
  grep -qxF "$pat" "$IG" || echo "$pat" >> "$IG"
done

# L1 热路径前置
git config --global credential.helper store

echo "[guards] pre-commit 守卫已就位: $HOOK"
echo "[guards] .gitignore 隔离条目已确认（幂等）"
echo "[guards] credential.helper=store 已确认"
