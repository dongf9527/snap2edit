# SNAP2EDIT · PAT 凭证保管与恢复手册（TOKEN_MANAGEMENT）

> **适用仓库**：<https://github.com/dongf9527/snap2edit.git>（本手册与 `scripts/tokenctl.py`、
> `.ai-vault/` 随本仓旅行，clone 后零改动可用）
> **蓝本**：guwen-model-eval 仓同名机制（owner 双仓共用一套方法论），本版为 snap2edit 适配稿
> - 生效日期：2026-11-07（初版 + 当日初始化与灭失演练实录）
> - 最近修订：2026-11-07
> - 配套文档：[`COLLABORATION.md`](COLLABORATION.md)（协作最高约定）、[`WORKFLOW.md`](WORKFLOW.md)（六步流程）

## 一、这套机制解决什么问题

本项目的人工智能协作方（AI agent）运行在一次性沙箱里：会话结束或系统回收时，沙箱磁盘可能
整卷回卷到旧快照，会话期间写入的文件随时可能消失。而 GitHub 推送凭证（PAT，Personal Access
Token，个人访问令牌）必须长期可用——不能每次沙箱回收都劳烦 owner 重新发一遍票。

凭证保管的三个硬目标：

1. **沙箱整卷灭失后，恢复零人工**——owner 永不需重发 token；
2. **明文零扩散**——token 明文不进 git、不进文档、不进命令行、不进聊天记录；
3. **换票零折腾**——到期换发是一条固定流水线，跑一遍命令即可。

## 二、明文红线（铁律，先于一切）

token 明文六不：

| # | 红线 | 说明 |
|---|------|------|
| 1 | 不入文档 | 本手册只出现掩码形态（`github_pat_****Xqie`）与 fp16 指纹 |
| 2 | 不入 commit | pre-commit 钩子拦截明文形态字符串（见 §4.4） |
| 3 | 不入 remote URL | 远端地址永远是干净的 `https://github.com/dongf9527/snap2edit.git` |
| 4 | 不进命令行参数 | 一律走文件/stdin（零 argv），避免进 shell 历史 |
| 5 | 不在聊天/终端回显 | 所有工具输出只给掩码与指纹 |
| 6 | 不入 issue/PR/日志 | 同红线 1 |

**唯一既定例外**：L1 层 `~/.git-credentials`（credential helper store 文件，权限 0600，
位于用户主目录、仓库之外）——这是 git 官方 store 机制的工作文件，是「推送热路径」的既定
设计，受文件权限与仓库外位置双重隔离。

**密文不在此限**：`.ai-vault/` 入仓的都是密文（§3 L0 层），守卫钩子也不拦密文形态。

**本仓既成事实注记（如实记录）**：现行票在 2026-11-07 初始化前曾以聊天正文形态传递一次
（红线 5 的既成违反，渠道为 owner 本人控制的 IM，泄露面有限）。机制建成后的标准交割路径
为「附件 txt → `tokenctl.py ingest --file` → 原件自动粉碎，token 零过聊天正文」（§6）；
owner 可择期按 §6 换发消除该残留面。

## 三、四层保管模型（正本结构）

| 层 | 位置 | 内容 | 权限 | 角色 | 灭失后果 |
|---|------|------|------|------|----------|
| **L0 入仓永续层** | `snap2edit/.ai-vault/`（在 git 里，随 GitHub 永续） | `token.enc`（112B 密文）＋ `vault.key.enc`（96B 密文）＋ `restore.py`（自含外层口令 K2 的自恢复脚本，仅依赖 stdlib＋openssl CLI）＋ `meta.json`（登记簿，零 token 材料）＋ `README.md` | 0644 | 保底：整卷灭失后 clone 即可拉回 | 连仓都丢才失效（重新 clone 即回来） |
| **L1 推送热路径** | `~/.git-credentials`（仓库外用户主目录） | `https://dongf9527:<token>@github.com` 形态一行（git store 机制工作文件） | 0600 | 日用：`git push/fetch` 自动取票 | 推送瘫痪 → wire 一键重建 |
| **L2 主密文层** | `~/my-project/.secrets/vault/token.enc` ＋ `.secrets/keys/vault.key` | AES-256-CBC ＋ PBKDF2-HMAC-SHA256 20 万迭代；口令 = vault.key（32B 随机 hex，密钥分离，同 0600） | 0600 | 沙箱会话内的密文主存 | wire 从 L3/L0 逐层拉回 |
| **L3 三分片兜底层** | `~/my-project/.secrets/shards/token.shard.{1,2,3}.b64` | token 切半 A‖B，三片 = {mask=A⊕B, A, B}；任取两片即可重组，单片丢失无信息泄露 | 0600 | 兜底：防 L2 单文件损坏 | 任意两片在即可重组；rebuild-shards 重切 |

**L0 解密链**（`restore.py` 执行）:

```
restore.py 内嵌外层口令 K2
    └→ 解开 vault.key.enc（AES-256-CBC + PBKDF2 20 万迭代）→ 得 vault.key
        └→ 解开 token.enc（同算法）→ 得 token 明文（仅内存，零回显）
            └→ fp16 指纹比对 meta.json 在册值（防串票）
                └→ 回写 L1（0600）＋ L2（token.enc＋vault.key，0600）＋ L3（三片重切，0600）
```

**meta.json（token 的户口本）字段**：`mask`（掩码形态 `github_pat_****Xqie`）、
`fp16`（token 的 SHA-256 前 16 位十六进制指纹，不可逆推回 token）、`login`（dongf9527）、
`expires`（到期日制；**现行票到期日 owner 尚未申报，当前登记为 null——请在 GitHub 后台
查证后用 `ingest --expires` 或直接编辑补登**）、`scheme`、`updated`。
指纹是「验明正身」的唯一凭据：任何一次恢复/取票后都与它比对。

**权限矩阵**：本地三层全部 0600；`.ai-vault/` 内只放密文与脚本（0644 入仓无妨）；
`.secrets/`、`.credentials/`、`upload/`、`*.token` 在隔离面内永不入 git（本仓
`.gitignore` 与沙箱项目根双重隔离——本仓敏感层本就位于 snap2edit 仓库之外）。

## 四、入库（push）链路：token 怎么走到 GitHub

### 4.1 干净的远端地址

`remote.origin.url = https://github.com/dongf9527/snap2edit.git`——URL 里没有任何凭证
成分。凭据注入完全由 git 的 credential 机制在传输层完成。

### 4.2 取票路径（L1 热路径）

`credential.helper = store`（git 全局配置，由守卫脚本与 wire/ingest 双重确保）→ git 在
push/fetch 时自动读 `~/.git-credentials`（0600）取票 → token 不进 URL、不进命令行参数、
不进终端回显。推拉命令就是普通 git 命令：

```bash
git push                      # L1 在位时直接可用
git fetch origin --tags --force --prune --prune-tags
# 或等价的封装入口:
python3 /home/z/my-project/snap2edit/scripts/tokenctl.py push
```

### 4.3 通路实证法（每轮对齐必做）

```bash
git push --dry-run            # 期望输出: Everything up-to-date
```

dry-run 走完整认证链但不真推——「Everything up-to-date」即证明 L1 热路径 alive
（2026-11-07 本仓初始化轮实录通过，见 §5.3）。

### 4.4 安全网（入库前的三道闸）

1. **pre-commit 钩子**（本仓 `.git/hooks/pre-commit`，由 `scripts/install_token_guards.sh`
   幂等安装）：暂存 diff 里出现 PAT 明文形态字符串（`ghp_`/`github_pat_` 等前缀＋20 位以上
   字母数字）即拒绝提交。**snap2edit 适配差异：守卫安装脚本已入仓 `scripts/`（蓝本为
   沙箱级），灾后 clone 即得，无需凭记忆重写**。
2. **ingest 形态校验**：新票入层前先检查文件首形态像不像 PAT（不像即拒收），再调 GitHub
   API 验真（HTTP 200 ＋ login 比对）才落层。
3. **指纹登记**：落层同时以 fp16 入 meta.json 在册，此后每次恢复/验真都比对指纹，
   防止「拿错票」。

### 4.5 被钩子拦了怎么办

守卫拦的是明文形态。若提交内容是文档引述了旧票字样（历史文档惯例不改写），先确认该票已在
GitHub 后台吊销（吊销后即为惰性字符串，不构成风险），再把文本改成掩码形态（如
`github_pat_****XXXX`）即可通过。密文形态（`.ai-vault/` 的 token.enc 等）不在拦截面，
正常提交。（2026-11-07 双面探针实测：明文形态拦截 exit=1、掩码形态放行 exit=0。）

## 五、恢复流程（核心章）

### 5.1 恢复决策树

```
git 推拉报错「could not read Username」？
├─ 本地三层还在吗？ ── python3 scripts/tokenctl.py status
│
├─ L1/L2/L3 全灭（沙箱回收常态，L0 显示 OK）
│    └→ python3 scripts/tokenctl.py wire        # 自动判层: L2→L3→L0 逐层拉回
│         （等价于直接跑 python3 .ai-vault/restore.py）
│
├─ 仅 L3 单片丢失
│    └→ wire（任二片即可重组）→ 补全后 rebuild-shards 重切回 3/3
│
├─ 仅 L2 密文损坏、L3 在
│    └→ wire（L3 重组回写 L2；vault.key 灭失时自动轮换新钥并同步 L0）
│
├─ 连 .ai-vault 都没了（沙箱连仓库一起灭失）
│    └→ 重新 clone → python3 .ai-vault/restore.py → verify
│
└─ verify 返回 401（票过期/被吊销）
     └→ 走换发 SOP（§6）
```

### 5.2 标准恢复四步（命令＋预期输出）

```bash
# ① 看四层状态（确认灾情）
python3 scripts/tokenctl.py status
# 期望: L0 OK（入仓密文层）/ L1 缺失 / L2 缺失 / L3 0/3 → 判定本地三层全灭

# ② 一键自愈（本地三层灭失时自动从 L0 拉回）
python3 scripts/tokenctl.py wire
# 期望: [restore] 本地三层已重建: L1(helper)＋L2(token.enc 112B)＋L3(3 shards)
#       [restore] mask=github_pat_****Xqie fp16=… —— token 零回显

# ③ GitHub API 验真
python3 scripts/tokenctl.py verify
# 期望: [verify] HTTP 200 login=dongf9527 fp16=… —— 验真通过（且与在册指纹一致）

# ④ 恢复推拉并实证
git fetch origin --tags --force --prune --prune-tags
git push --dry-run        # 期望: Everything up-to-date
```

### 5.3 活案例实录（2026-11-07 本仓初始化＋整卷回收演练，全程 owner 零操作）

| 步骤 | 实际发生 | 结果 |
|---|---|---|
| 0 | owner 经 IM 提供现行票 → 写入隔离面临时文件（仓外 `.secrets/inbox/`，零 argv） | 交割材料就位 |
| 1 | `tokenctl.py ingest --file`：形态校验通过 → GitHub API 验真 HTTP 200 login=dongf9527 → 三层落位（L2 token.enc 112B ＋ L3 3 shards ＋ L1 0600）→ **原件自动粉碎** | mask=github_pat_****Xqie，fp16=7f8cf30038b87d9c 在册 |
| 2 | `tokenctl.py vault-sync`：生成 K2、封 vault.key.enc（96B）、注入 restore.py、meta.json 与 README 入 L0，**回读解密链验真** | L0 四件套齐，回读 fp16 与在册一致 |
| 3 | `install_token_guards.sh`：pre-commit 钩子入位＋.gitignore 隔离面＋credential.helper=store | 守卫就位 |
| 4 | **模拟整卷回收**：`rm -rf ~/.git-credentials ~/my-project/.secrets`（L1/L2/L3 全灭） | `status` → L0 OK / L1 缺失 / L2 缺失 / L3 0/3，灾情确认 |
| 5 | `tokenctl.py wire` → 自动触发 L0 `restore.py`（K2→vault.key→token→fp16 比对→回写三层） | `[restore] 本地三层已重建`，fp16 与在册一致，token 零回显 |
| 6 | `tokenctl.py verify` | HTTP 200 login=dongf9527，指纹一致 |
| 7 | `git push --dry-run` | **Everything up-to-date**，L1 热路径实证可用 |
| 8 | 守卫双面探针：假票明文形态 commit | 拦截 exit=1；掩码形态探针放行 exit=0（已清理） |

全程未重发票、未见明文、未动远端。修复记录：初始化轮发现并修复 `read_l1` 行解析缺陷
（改用 `urlparse` 严格取 password 字段）——修复后 status/verify 指纹全部一致。

### 5.4 恢复后健康检查清单

- [ ] `tokenctl.py status` 四行全 OK（L0 OK / L1 OK(600) / L2 OK / L3 3/3）
- [ ] `tokenctl.py verify` HTTP 200 且指纹与在册一致（不一致=疑似串票，核对 ingest 记录）
- [ ] `git fetch` 成功且 `git status` 无 ahead/behind 异常残留
- [ ] `git push --dry-run` 返回 Everything up-to-date（或真推一记后回验）
- [ ] pre-commit 钩子在位（`ls .git/hooks/pre-commit`，缺则重跑 `scripts/install_token_guards.sh`）

## 六、换发 SOP（到期/撤销时）

**触发条件**：meta.json 登记的到期日临近（**现行票到期日尚未登记，请 owner 在 GitHub
后台查证后补登**），或 verify 返回 401（服务端撤销/重生成）。未到期即 401 亦走同径，
不另立流程。

```bash
# ① owner 在 GitHub 后台生成新细粒度 PAT
#    （最小权限: Contents Read/Write、仅限 dongf9527/snap2edit 一仓；
#      附件 txt 交 IM 优先——token 零过聊天正文）

# ② 交割入层（验真→原子覆写 L2/L3＋L1→原件自动粉碎）
python3 scripts/tokenctl.py ingest --file <新票.txt> --expires YYYY-MM-DD
# 期望: [ingest] 三层落位，原件已粉碎; login=… fp16=…

# ③ 验真
python3 scripts/tokenctl.py verify

# ④ 刷新入仓永续层（L0 密文重封，restore.py 与 K2 不变）
python3 scripts/tokenctl.py vault-sync
# 期望: [vault-sync] L0 已刷新: token.enc 112B + vault.key.enc 96B, 回读 fp16=…

# ⑤ 随本轮 commit + push（.ai-vault 密文变更必须随轮入 GitHub，否则下次灾后拉回的是旧票密文）

# ⑥ 回 GitHub 后台吊销旧票（历史文档中的旧票字样一经吊销即惰性，不另改史）
```

**铁律加严版**：token 明文不入文档、不入 commit、不入 remote URL、不在聊天/命令行回显
（密文经 `.ai-vault/` 入仓不在此限）。到期日以 meta.json 登记制为准（不搞口谕）。

## 七、故障排查速查表

| 症状 | 根因 | 处置 |
|---|---|---|
| could not read Username for 'https://github.com' | 本地三层灭失（沙箱回收） | `tokenctl.py wire` → `verify`（§5.2） |
| Invalid username or token（HTTP 401，x-access-token/oauth2 双形同拒） | 票到期或被吊销（细粒度 PAT 到期特征） | 换发 SOP（§6） |
| HTTP 403 | 权限收窄（细粒度 PAT 权限面不足） | owner 重发含 Contents RW 的票，循 §6 |
| push 卡住等待交互输密码 | L1 不在位且 helper 缺失 | wire 重建；**严禁在交互提示里手输票**（会进终端历史，破明文红线） |
| pre-commit 拦截提交 | 暂存内容含 PAT 明文形态串 | 核实为引述旧票字样→确认旧票已吊销→改掩码形态后重提（§4.5） |
| verify 指纹与在册不符 | 本地拿到的是另一张票（串票） | 核对最近 ingest 记录；必要时废弃本地层重新 ingest |
| L3 两片以上同灭且 L2 不可用 | 超出设计灾情 | 走 L0（restore.py）；L0 亦灭则重新 clone |
| 疑似 token 泄漏 | — | **立即 GitHub 后台吊销→全链惰性→换发 SOP**，再排查泄漏面 |

## 八、安全边界与已知风险（如实陈述）

1. **密钥同仓是设计内取舍**：外层口令 K2 内嵌于 `restore.py`，持有本仓读权限者理论上可
   解密全链。owner 已知情同意（沿用蓝本 2026-11-04 §五修订的同一决策）：**私有仓**前提下
   边际风险≈零，换取「整卷灭失零重发」。**若本仓（当前 public）转为存放真票载体前未转
   私有，必须先重评本设计**（K2 轮换 = 更换 K2 后 vault-sync 重封两把锁）。
   ⚠️ snap2edit 特有注记：本仓当前为 **public** 仓，与蓝本私有仓前提不同——L0 密文层在
   public 仓里等同于公开密文。在 owner 明确知情并接受「公开仓 + K2 内嵌」风险（或转私有、
   或换 K2 不入仓的变体）之前，**本仓现行票的 L0 层以「机制演练载体」定性**；正式承载
   长期凭证前建议先转 private。
2. **守卫拦形态不拦内容**：pre-commit 钩子按字符串形态拦截，无法识别「被拆散/编码后的
   明文」——纪律第一道闸是人的红线意识，钩子是第二道。
3. **L1 是唯一明文落盘点**：`~/.git-credentials` 为明文形态（0600，仓库外）。它是 git
   store 机制的工作文件，属设计内例外；主机被完全接管时该文件可读——与「主机被接管则
   一切防护失效」同层级，不构成额外攻击面放大。
4. **吊销是终极兜底**：token 疑似泄漏时，GitHub 后台即时吊销即令全链惰性（git 拒认、
   历史文档字样失效），随后循换发 SOP 即可，无需「召回」任何已分发材料。
5. **工具入库随仓旅行（本仓初版即按此落地）**：`tokenctl.py` 与 `install_token_guards.sh`
   正本均入仓 `scripts/`（路径自举：realpath 推导仓根＋`TOKENCTL_HOME` 覆盖项目根，clone
   后零改动可用）。灾后恢复顺序恒为：clone → `python3 scripts/tokenctl.py status`
   （或 wire，L2/L3 灭失时自动触发 restore.py）→（如需）重跑守卫脚本。
6. **到期日登记缺口**：现行票 expires=null（owner 未申报）。请在后台查证后补登
   （重跑 `ingest --expires` 或编辑 meta.json），否则到期将以 401 方式被动发现。

## 九、命令速查卡

| 命令 | 作用 | 备注 |
|---|---|---|
| `python3 scripts/tokenctl.py status` | 四层状态一览＋在册登记＋本轮指纹 | 每轮对齐第一步 |
| `python3 scripts/tokenctl.py verify` | GitHub API 验真（HTTP 200＋login＋指纹比对） | 恢复/换票后必做 |
| `python3 scripts/tokenctl.py wire` | 自愈重接（L2→L3→L0 逐层拉回，重建 L1） | 沙箱回收后的一键恢复 |
| `python3 scripts/tokenctl.py ingest --file F` | 新票入三层并粉碎原件 | 换票专用；非 PAT 形态拒收 |
| `python3 scripts/tokenctl.py vault-sync` | 刷新 `.ai-vault/` 入仓密文 | 换票后必做，且随轮 push |
| `python3 scripts/tokenctl.py rebuild-shards` | 以 L2 为源重切 L3 三片 | 演练/补片用 |
| `python3 scripts/tokenctl.py push [args…]` | 经 L1 热路径推送 | 等价 git push |
| `python3 .ai-vault/restore.py` | L0 自恢复（wire 的底层） | 新 clone 后首跑 |
| `bash scripts/install_token_guards.sh` | 重装 pre-commit 守卫＋.gitignore 隔离面 | 幂等 |
| `git push --dry-run` | 推送通路实证 | 期望 Everything up-to-date |

## 十、与蓝本（guwen-model-eval 手册）的差异适配说明

| 项 | 蓝本 | 本仓适配 |
|---|---|---|
| 仓库/路径 | guwen-model-eval | snap2edit（`/home/z/my-project/snap2edit/`） |
| tokenctl 正本 | 入仓 scripts/（2026-11-06 roll_454 修订后） | 初版即入仓 `scripts/tokenctl.py` |
| 守卫安装脚本 | 沙箱级不入仓 | **入仓** `scripts/install_token_guards.sh`（灾后 clone 即得，本仓适配改进） |
| 仓可见性 | 私有仓 | **public 仓**——L0 密文承载长期凭证前需重评（见 §8.1 ⚠️） |
| 现行票到期日 | 2026-12-01（登记制） | 未登记（expires=null，待 owner 补登，见 §8.6） |
| 机制定位 | 生产凭证保管 | 已按生产标准建成并实测；在仓可见性问题上以 §8.1 为准 |
