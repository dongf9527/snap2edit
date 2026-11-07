# 仓库协作规则（COLLABORATION）

> 本规则是 Snap2Edit 仓库所有协作行为的**最高约定**：沙箱与 GitHub 之间如何同步、
> 如何提交、哪些操作绝对禁止。任何会话内的改动都必须遵守本表执行。
>
> - 生效日期：2026-11-03
> - 最近修订：2026-11-07（规则 2 仓库位置调整）
> - 适用范围：`https://github.com/dongf9527/snap2edit.git` 及其全部本地克隆

## 核心规则表

| # | 规则 | 说明 |
|---|------|------|
| 1 | **唯一同步方式** | 所有代码/文档改动通过 `git commit` + `git push` 推送到 GitHub，不在对话中凭空产生代码 |
| 2 | **仓库位置** | `/home/z/my-project/snap2edit/`（远程：<https://github.com/dongf9527/snap2edit.git>），不在其他目录创建 `.git`（2026-11-07 注记：原 `/home/z/my-project/download/snap2edit/` 同步废弃，全库仅以本路径为准） |
| 3 | **提交规范** | 小步提交，commit message 使用 conventional commits 风格（`feat:` / `fix:` / `docs:` / `refactor:` / `chore:` / `test:`） |
| 4 | **会话记录** | 分析/评估/测试记录写入 `docs/` 目录，以 Markdown 形式提交推送 |
| 5 | **禁止 force push** | 绝不使用 `git push --force`；同理禁止对已推送 commit 执行 `--amend` 后再推送（等效 force，同样触犯本条，2026-10-24 注记）；未推送 commit 的 amend 属修正笔误常规手段，不受限 |
| 6 | **Rebase 前置** | rebase 前先评估替代方案（revert/merge），必要时提前告知确认 |
| 7 | **bug 修复不重命名变量** | 修复 bug 时保持原变量名，仅在 refactor 时重命名 |

## 补充说明

**同步操作标准动作**（规则 1 的落地步骤）：

```bash
cd /home/z/my-project/snap2edit            # 规则 2：唯一仓库位置
git pull --ff-only                          # 先拉齐远程（禁止 merge commit 式拉取）
# ... 本地修改 ...
git add <files>
git commit -m "docs: ..."                   # 规则 3：conventional commits
git push origin main                        # 推送；绝不加 --force（规则 5）
```

**双向一致性核对**：每次同步后用以下命令确认沙箱与 GitHub 一致，两边 HEAD 必须相同：

```bash
git log --oneline -1                        # 本地 HEAD
git ls-remote origin refs/heads/main        # 远程 main
git status --short                          # 工作区必须干净（无未提交改动）
```

**凭据安全**：推送凭据仅内嵌在单次 push URL 中使用，不写入 remote 配置、不落盘；
命令输出一律经脱敏处理（token 替换为 `[REDACTED]`）后才进入会话记录。

**会话产物归档**（规则 4 的落地约定）：

- 分析/评估/测试记录 → `docs/`（如本文件、PRD.md、WORKFLOW.md）
- 复刻案例 → `docs/<案例名>/`（原图 + `*.html` + `*.pptx` + 预览 + README）
- 过程脚本与对比证据 → `docs/workbench/`
- 约定：**以仓库为准**——凡未提交推送的内容视为不存在。
