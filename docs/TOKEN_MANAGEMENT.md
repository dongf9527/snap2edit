# SNAP2EDIT · PAT 凭证保管与恢复手册（TOKEN_MANAGEMENT）

> **适用仓库**：<https://github.com/dongf9527/snap2edit.git>（**public**）
> **版本**：v2（2026-11-07 公开仓适配重评版）——v1 当日落地当日出安全事件，全程复盘见 §八
> **蓝本**：guwen-model-eval 仓同名机制；本版为其公开仓适配稿（差异表见 §十）
> **配套机件**：`scripts/tokenctl.py` · `scripts/install_token_guards.sh` · `.ai-vault/`（登记簿）
> **配套文档**：[`COLLABORATION.md`](COLLABORATION.md)（协作最高约定）、[`WORKFLOW.md`](WORKFLOW.md)

## 〇、v2 修订摘要（为什么重评）

v1（2026-11-07 13:48 UTC，提交 `61c3fe7`）按蓝本把 L0 密文链整体入仓：
`token.enc`（票密文）＋ `vault.key.enc`（密钥密文）＋ `restore.py`（**内嵌外层口令 K2**）。
蓝本前提是**私有仓**；本仓是 **public**。当日取证审计实证（全程零回显）：

| 取证项 | 结果 |
|---|---|
| 仓库未认证可达 | `GET github.com/dongf9527/snap2edit` → HTTP 200（公开确认） |
| 公开链可复原性 | clone → 运行 `restore.py` → 离线复原出票，fp16=`7f8cf30038b87d9c` 与在册一致 |
| 票据状态（审计时点） | HTTP 200 login=dongf9527——票仍有效，未被 GitHub 自动吊销 |

**结论**：「密文＋密钥密文＋内嵌口令」三件套放进公开仓＝**等同明文公开**。

**v2 处置**（本提交完成）：

1. 密文链移出工作区与索引。⚠️ 历史提交 `61c3fe7` 中的旧密文仍可取出——**旧票在 GitHub
   后台吊销后即惰性**（吊销优先于一切，见 §8.3）；
2. L0 降级为**登记簿层**（零密文：`meta.json` ＋ `README.md`）；
3. L2/L3 收进本仓 `.secrets/` gitignore 隔离区（v1 曾误写外层自动化工作区并被其提交）；
4. 恢复链改为 L2→L3 本地自愈；L2/L3 俱灭 → owner 后台重发（**吊销＋重发是终极兜底**）。

**行动项（owner）**：尽快在 GitHub → Settings → Developer settings → Fine-grained tokens
吊销现行票 `github_pat_****Xqie`（自 13:48 UTC 起公开可复原，且曾经聊天通道传递），随后按 §六换发。

## 一、这套机制解决什么问题

本项目的人工智能协作方（AI agent）运行在一次性沙箱里：会话结束或系统回收时，沙箱磁盘可能
整卷回卷到旧快照，会话期间写入的文件随时可能消失。而 GitHub 推送凭证（PAT，Personal Access
Token，个人访问令牌）必须长期可用——不能每次沙箱回收都劳烦 owner 重新发一遍票。

凭证保管的四个硬目标（v2 排序调整）：

1. **公开仓零可复原材料**（v2 新升为第一硬目标）——仓库公开的每一字节都不构成攻击面；
2. **明文零扩散**——token 明文不进 git、不进文档、不进命令行、不进聊天记录；
3. **沙箱回收后恢复近零人工**——本地三层在位时 `wire` 一键自愈；仅 L2/L3 俱灭才需 owner 重发；
4. **换票零折腾**——到期换发是一条固定流水线，跑一遍命令即可。

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
位于用户主目录）——git 官方 store 机制的工作文件，是「推送热路径」的既定设计。

**v2 加严：密文也不入公开仓**。v1 曾认为「密文入仓无妨，守卫钩子不拦密文形态」——在私有仓
前提下成立，在 public 仓不成立（密文链三件套可离线复原，见 §〇）。故 v2 起任何 token 材料
（明文**和**密文）一律不入 git；L0 只保留登记簿。

**本仓既成事实注记（如实记录，详证见 §8.1）**：现行票在 2026-11-07 初始化前曾以聊天正文
形态传递一次（红线 5 违例）；同日 13:48 UTC v1 又把密文链推入公开仓（红线「密文不入公开仓」
违例，等同红线 1-6 的复合暴露）。两条违例的终局解法都是**吊销＋换发**（§六）。

## 三、四层保管模型（v2 正本结构）

| 层 | 位置 | 内容 | 权限 | 角色 | 灭失后果 |
|---|------|------|------|------|----------|
| **L0 入仓登记层** | `snap2edit/.ai-vault/`（在 git 里，随仓库旅行） | `meta.json`（户口本：mask/fp16/login/expires/layers）＋ `README.md`。**零密文、零口令** | 0644 | 审计基准＋恢复手册指针 | 连仓都丢才失效（重新 clone 即回来） |
| **L1 推送热路径** | `~/.git-credentials`（用户主目录） | `https://dongf9527:<token>@github.com` 一行 | 0600 | 日用：`git push/fetch` 自动取票 | 推送瘫痪 → `wire` 一键重建 |
| **L2 主密文层** | `snap2edit/.secrets/vault/token.enc` ＋ `.secrets/keys/vault.key` | AES-256-CBC ＋ PBKDF2-HMAC-SHA256 20 万迭代；口令=vault.key（32B 随机 hex，密钥分文件存放） | 0600（目录 0700） | 沙箱内的密文主存 | `wire` 从 L3 拉回 |
| **L3 三分片兜底层** | `snap2edit/.secrets/shards/token.shard.{1,2,3}.b64` | token 切半 A‖B，三片 = {mask=A⊕B, A, B}；任取两片即可重组 | 0600 | 兜底：防 L2 单文件损坏 | 任意两片在即可重组 |

**隔离面（v2 关键变化）**：L2/L3 位于**本仓目录内**但被三重隔离——`.gitignore` 的
`.secrets/` 条目、pre-commit 守卫（`.secrets/**` 一律拒收）、以及「提交前 `git status`
人工确认」惯例。选择仓内而非仓外的原因：v1 曾把 L2/L3 写到仓外路径 `/home/z/my-project/`，
而该路径是自动化工作区仓（.secrets 曾被其提交跟踪）——仓内隔离区反而更可控，且随
`/home/z/my-project/` 持久区在沙箱回收间存活。

**恢复链（v2）**：

```
git 推拉报错「could not read Username」？
├─ tokenctl status 看灾情
├─ L2 在      → wire   （L2→L1，秒级自愈，顺带重切 L3）
├─ 仅 L3 在   → wire   （任二片重组 → 重封 L2 → L1 → vault-sync 刷新登记簿）
├─ L2+L3 俱灭 → owner 后台重发票 → ingest（吊销旧票是前置动作，§六）
└─ verify 401 → 换发 SOP（§六）
```

**meta.json（token 的户口本）字段**：`mask`（掩码形态）、`fp16`（token 的 SHA-256 前 16 位
十六进制指纹，不可逆推回 token）、`login`、`expires`（到期日；**现行票 owner 尚未申报，
当前登记为 null——请在后台查证后用 `ingest --expires` 或直接编辑补登**）、`layers`（四层
清单）、`updated`。指纹是「验明正身」的唯一凭据：任何一次恢复/取票后都与它比对。

## 四、入库（push）链路：token 怎么走到 GitHub

### 4.1 干净的远端地址

`remote.origin.url = https://github.com/dongf9527/snap2edit.git`——URL 里没有任何凭证
成分。凭据注入完全由 git 的 credential 机制在传输层完成。

### 4.2 取票路径（L1 热路径）

`credential.helper = store`（全局配置，由守卫脚本与 wire/ingest 双重确保）→ git 在
push/fetch 时自动读 `~/.git-credentials`（0600）取票 → token 不进 URL、不进命令行参数、
不进终端回显。推拉命令就是普通 git 命令：

```bash
git push
git fetch origin --tags --force --prune --prune-tags
# 或等价的封装入口（输出强制脱敏）:
python3 scripts/tokenctl.py push origin main
```

### 4.3 通路实证法（每轮对齐必做）

```bash
git push --dry-run            # 期望输出: Everything up-to-date
```

dry-run 走完整认证链但不真推——「Everything up-to-date」即证明 L1 热路径 alive
（2026-11-07 v2 重整轮实录通过，见 §8.1）。

### 4.4 安全网（入库前的三道闸）

1. **pre-commit 钩子**（本仓 `.git/hooks/pre-commit`，由 `scripts/install_token_guards.sh`
   幂等安装）：暂存 diff 里出现 PAT 明文形态串（`ghp_`/`github_pat_` 等前缀＋长字母数字）
   即拒绝提交；`.secrets/**` 一律拒收。
2. **ingest 形态校验＋API 验真**：新票入层前先检查形态像不像 PAT（不像即拒收），再调
   GitHub API 验真（HTTP 200 ＋ login 比对）才落层。
3. **指纹登记**：落层同时以 fp16 入 meta.json 在册，此后每次恢复/验真都比对指纹，
   防止「拿错票」。

### 4.5 被钩子拦了怎么办

守卫拦的是明文形态。若提交内容是文档引述旧票字样，先确认该票已在 GitHub 后台吊销
（吊销后即为惰性字符串，不构成风险），再把文本改成掩码形态（如 `github_pat_****XXXX`）
即可通过。（2026-11-07 实测：假票明文形态拦截 exit=1；掩码形态在 v2 提交中自然放行。）

## 五、恢复流程（核心章）

### 5.1 标准恢复四步（命令＋预期输出）

```bash
# ① 看四层状态（确认灾情）
python3 scripts/tokenctl.py status
# 期望: L0 OK(入仓登记簿) / L1 缺失 / L2 OK / L3 3/3 —— 典型灾情是仅 L1 灭（沙箱回收）

# ② 一键自愈
python3 scripts/tokenctl.py wire
# 期望: [restore] 源层=L2 → 本地三层已重建: L1(helper)+L2(token.enc 112B)+L3(3 shards)
#       [restore] mask=github_pat_****Xqie fp16=… —— token 零回显

# ③ GitHub API 验真
python3 scripts/tokenctl.py verify
# 期望: [verify] HTTP 200 login=dongf9527 fp16=… —— 验真通过（与在册指纹一致）

# ④ 恢复推拉并实证
git fetch origin --tags --force --prune --prune-tags
git push --dry-run        # 期望: Everything up-to-date
```

### 5.2 恢复后健康检查清单

- [ ] `tokenctl.py status` 四行全 OK（L0 OK(入仓登记簿) / L1 OK(600) / L2 OK / L3 3/3）
- [ ] `tokenctl.py verify` HTTP 200 且指纹与在册一致（不一致=疑似串票，核对 ingest 记录）
- [ ] `git fetch` 成功且 `git status` 无 ahead/behind 异常残留
- [ ] `git push --dry-run` 返回 Everything up-to-date（或真推一记后回验）
- [ ] pre-commit 钩子在位（`ls .git/hooks/pre-commit`，缺则重跑 `scripts/install_token_guards.sh`）
- [ ] 分片演练（季度）：`rebuild-shards` 后 `wire` 仍指纹一致

## 六、换发 SOP（到期/撤销/泄露时）

**触发条件**：meta.json 登记的到期日临近；或 verify 返回 401（服务端撤销/过期）；或
**疑似任何形式的暴露**（v2 加严：宁可错杀）。

```bash
# ⓪ 前置：GitHub 后台吊销旧票（若尚未吊销）——吊销令一切旧材料即刻惰性

# ① owner 在 GitHub 后台生成新细粒度 PAT
#    最小权限: Contents Read/Write、仅限 dongf9527/snap2edit 一仓、设到期日（≤90 天）
#    交割方式: 写入本仓隔离区文件（如 .secrets/inbox.pat）——token 零过聊天正文、零 argv

# ② 交割入层（验真→L2/L3/L1 落位→原件自动粉碎）
python3 scripts/tokenctl.py ingest --file .secrets/inbox.pat --expires YYYY-MM-DD
# 期望: [ingest] 三层落位…原件已粉碎; login=… fp16=…

# ③ 验真
python3 scripts/tokenctl.py verify

# ④ 刷新 L0 登记簿（零密文：只重写 meta.json + README.md）
python3 scripts/tokenctl.py vault-sync

# ⑤ 随本轮 commit + push（.ai-vault/ 登记变更随轮入 GitHub）

# ⑥ 更新本手册 §8.1 记录（换发时间、新票掩码/fp16、吊销完成标记）
```

## 七、故障排查速查表

| 症状 | 根因 | 处置 |
|---|---|---|
| could not read Username for 'https://github.com' | L1 灭失（沙箱回收常态） | `tokenctl.py wire` → `verify`（§5.1） |
| Invalid username or token（HTTP 401） | 票到期或被吊销 | 换发 SOP（§六） |
| HTTP 403 | 权限收窄（细粒度 PAT 权限面不足） | owner 重发含 Contents RW 的票，循 §六 |
| push 卡住等待交互输密码 | L1 不在位且 helper 缺失 | wire 重建；**严禁在交互提示里手输票**（会进终端历史） |
| pre-commit 拦截提交 | 暂存内容含 PAT 明文形态串或 .secrets/** | 按 §4.5 处置；确为真实凭据→立即吊销换发 |
| verify 指纹与在册不符 | 本地拿到的是另一张票（串票） | 核对最近 ingest 记录；必要时废弃本地层重新 ingest |
| L2/L3 俱灭（.secrets 被清） | 超出本地自愈能力 | owner 后台重发票（吊销＋重发是终极兜底） |
| 疑似 token 泄漏 | — | **立即 GitHub 后台吊销→全链惰性→换发 SOP**，再排查泄漏面并登记 §8.1 |

## 八、安全边界与威胁模型（v2 重评）

### 8.1 事件与换发记录（INCIDENT / ROTATION LOG）

**INCIDENT-2026-11-07：v1 密文链公开暴露**

| 时刻 (UTC) | 事件 |
|---|---|
| ~05:44 | 沙箱会话按蓝本初始化：ingest（票入 L1/L2/L3）→ vault-sync 封 L0 密文链 → 守卫就位 → 灭失演练（本地三层 rm 后经 L0 restore.py 拉回）→ `push --dry-run` 通过 |
| 13:48:09 | 提交 `61c3fe7`（密文链＋手册 v1＋工具）并推送。**公开仓从此任何人可离线复原票**（K2 内嵌于 restore.py，公开可读） |
| ~14:22 | 续会话取证审计：实证公开链可复原（复原票 fp16 与在册一致）；票仍有效（HTTP 200）。公开暴露窗口当时已 ~35 分钟 |
| ~14:30 | v2 处置：`git rm` 密文链；tokenctl v2（去 K2/密文链路、L2/L3 归位、push 脱敏）；手册 v2；票重入层（ingest→vault-sync→verify 全绿）；守卫假票拦截演练通过；本提交推送 |
| **待办** | **owner 在 GitHub 后台吊销现行票 `github_pat_****Xqie` → 按 §六换发 → 回填本行**（吊销完成前，`61c3fe7` 历史密文按「可复原」对待） |

**换发记录**（每次换发追加一行）：

| 日期 | 旧票处置 | 新票 mask / fp16 | expires | 经手 |
|---|---|---|---|---|
| （待 owner 吊销换发后回填） | | | | |

### 8.2 公开仓威胁模型（防得住 / 防不住，如实陈述）

| 防得住 | 防不住 |
|---|---|
| 公开仓浏览/clone 者——零密文、零口令可取 | 拥有沙箱整盘读权限的攻击者（L2 密钥与密文同盘分文件） |
| 单文件泄露（token.enc 泄露无 vault.key 不可解） | 沙箱快照级整卷泄露（L2+L3 同盘共存） |
| 误提交 `.secrets/**`（gitignore＋pre-commit 双闸） | owner 自身的聊天通道泄密（只能靠流程纪律） |
| 明文形态入库（钩子形态拦截） | 被拆散/编码后的明文（形态拦不住，靠红线意识） |
| 串票（fp16 比对在册指纹） | GitHub 侧票据权限过大（靠最小权限发票约束） |

**残余风险处置**：L2/L3 同盘共存的残余风险由换发 SOP 兜底——一旦怀疑泄露，立即吊销换发，
损失窗口以分钟计。吊销是终极兜底：token 被吊销即令全链材料（明文、密文、分片、历史提交
中的旧密文）全部惰性，随后循 §六即可，无需「召回」任何已分发材料。

### 8.3 历史提交中旧密文的惰性条件

`61c3fe7` 中的 `token.enc / vault.key.enc / restore.py(K2)` 在**旧票吊销后**变为：
不可解的密文（密钥对旧票无意义）＋ 无攻击价值的脚本。协作规则 5 禁止 force push，
故不做历史重写——**吊销优于清史**，这也是本手册把「立即吊销」列为事件响应第一动作的原因。

### 8.4 其他边界

1. **守卫拦形态不拦内容**：无法识别拆散/编码后的明文——纪律第一道闸是人的红线意识，钩子是第二道。
2. **L1 是唯一明文落盘点**：`~/.git-credentials` 为明文形态（0600）。它是 git store 机制的
   工作文件，属设计内例外；主机被完全接管时该文件可读——与「主机被接管则一切防护失效」
   同层级，不构成额外攻击面放大。
3. **到期日登记缺口**：现行票 expires=null（owner 未申报）。请在后台查证后补登
   （重跑 `ingest --expires` 或编辑 meta.json），否则到期将以 401 方式被动发现。
4. **工具入库随仓旅行**：`tokenctl.py` 与 `install_token_guards.sh` 正本均入仓 `scripts/`
   （路径自举：realpath 推导仓根；敏感层默认 `<repo>/.secrets/`，可用 `TOKENCTL_HOME` 覆盖）。

## 九、命令速查卡（v2）

| 命令 | 作用 | 备注 |
|---|---|---|
| `python3 scripts/tokenctl.py status` | 四层状态＋在册登记＋本轮指纹 | 每轮对齐第一步 |
| `python3 scripts/tokenctl.py verify` | GitHub API 验真（HTTP 200＋login＋指纹比对） | 恢复/换票后必做 |
| `python3 scripts/tokenctl.py wire` | 自愈重接（L2→L3 逐层拉回，重建 L1） | 沙箱回收后的一键恢复 |
| `python3 scripts/tokenctl.py ingest --file F [--expires D]` | 新票入三层并粉碎原件 | 换票专用；非 PAT 形态拒收 |
| `python3 scripts/tokenctl.py vault-sync` | 刷新 `.ai-vault/` 登记簿（零密文） | 换票后必做，随轮 push |
| `python3 scripts/tokenctl.py rebuild-shards` | 以 L2 为源重切 L3 三片 | 演练/补片用 |
| `python3 scripts/tokenctl.py push [args…]` | 经 L1 热路径推送（输出强制脱敏） | 等价 git push |
| `bash scripts/install_token_guards.sh` | 重装 pre-commit 守卫＋.gitignore 隔离面 | 幂等 |
| `git push --dry-run` | 推送通路实证 | 期望 Everything up-to-date |

## 十、与蓝本（guwen-model-eval 手册）的差异适配说明（v2）

| 项 | 蓝本（私有仓前提） | 本仓 v2（public） |
|---|---|---|
| L0 | 密文链入仓＋K2 内嵌 restore.py，clone 即得全链 | **登记簿（零密文）**；密文链已随事件移除（§8.1） |
| L2/L3 位置 | 沙箱项目根 `.secrets/`（仓外） | **本仓 `.secrets/`**（gitignore＋钩子双重隔离；v1 仓外路径是自动化工作区仓，已纠正） |
| 恢复链 | L1→L2→L3→L0 四级自愈 | L1→L2→L3 三级自愈；全灭 → owner 重发 |
| 终极兜底 | L0 入仓永续（整卷灭失零重发） | **吊销＋重发**（GitHub 后台一分钟；公开仓的必然取舍） |
| 第一硬目标 | 灭失零重发 | **公开仓零可复原材料**（灭失零重发退居其后） |
| push 输出 | 脱敏约定 | `tokenctl push` 强制脱敏（代码级保证） |
| 守卫安装脚本 | 入仓 `scripts/` | 入仓（v1 既有适配，保留） |
| 现行票到期日 | 2026-12-01（登记制） | 未登记（expires=null，待 owner 补登，§8.4） |
