# ROTATE · 倾斜元素全链路（引擎字段 → studio 读出气泡 → VLM 抽取）

> v0.2.1 rotate 字段 + v0.5 变换手柄 + v0.6 角度实时读出气泡 + VLM 倾斜抽取。
> 一句话：**一张图里的倾斜元素，现在能被识别（rotate 抽取）、被编辑（旋转手柄+读数）、被双产线还原（SVG transform ⇄ PPTX rotation）。**

## 1. 字段语义（引擎侧，src/snap2edit/spec.py）

- `rotate`：可选数字，**度、顺时针**；归一化到 `[0,360)`、保留一位小数。
- 旋转中心：盒子（rect/rrect/pill/circle）绕自身中心；自由文本绕锚点；线段/箭头**不支持**
  （几何完全由端点 x1/y1/x2/y2 承载，rotate 键被忽略并剔除）。
- 双产线同语义：产线① SVG `transform=rotate(...)` ⇄ 产线② PPTX `shape.rotation`
  （自由文本按「中心绕锚点旋转」重定位，与 SVG 精确一致）。

## 2. studio 编辑器（web/app/studio/editor.tsx）

- 旋转手柄：单选绕自身中心/锚点/中点；多选各元素绕组中心公转+自转（数学精确等价）；
  Shift 15° 步进；松手一次性烘焙进 YAML（交互全程 DOM transform，不重渲 SVG）。
- **角度实时读出气泡（v0.6）**：按住旋转手柄即出现，跟随指针（画布坐标百分比定位，
  悬于光标上方），松手消失。文案与烘焙同口径：
  - 单选盒子/文本：`∠ 终角°（Δ 增量°）`（终角=归一化后的 bake 结果）；
  - 线段：只有 `Δ`（rotate 键不生效）；
  - 多选：`Δ · N个`；
  - Shift 按住时附 `15°步进` 提示。
  - 实现：`rotHudText()`（模块级纯函数，与 bakeRotate 同一归一化公式）；
    指针动 ≥2px 或文案变化才 setState，重渲染零负担。

## 3. VLM 抽取（web/lib/spec.ts，/api/spec 与 /api/refine 共用）

- **系统提示词**：倾斜/旋转的元素（斜置卡片、斜标签、斜排文字、斜色带）必须估出
  顺时针角度写入可选字段 `rotate`（数值，度，`[0,360)`，一位小数以内）；
  水平/垂直元素不写；line/arrow 不写（倾斜由端点表达）；角度容差 ±5°。
- **normalizeSpec**（1.5 步，与引擎同源）：线段/箭头剔除 rotate 键；数字归一化
  `[0,360)`；0 删键；非法值保留交校验器报错 → /api/spec 自动回询重试一次。
- **validateSpecYaml**（门 0 TS 同源）：非数字 → error；越界 → 仅告警（引擎会归一化）；
  线段带 rotate → 仅告警；合法值零噪音。
- **buildFixPrompt**：修正提示补「rotate 非法→改为 0-360 的数字或删除该键」，
  refine 自动迭代同样能修复 rotate 类错误。

## 4. 测试矩阵（本轮实测）

| 层级 | 用例 | 结果 |
|---|---|---|
| 单元（`web/tests/spec.rotate.test.ts`，`node --test` 原生跑 TS） | 提示词规则 / 剔除备注 / 归一化 370→10、-10→350、0 删键 / 非法保留 / 校验分级 | **5/5** |
| studio E2E（scripts/studio_e2e4.py） | 按下即现 Δ±0° → 45°/90° 实时更新 → 松手烘焙+气泡消失；Shift 步进提示与量化；线段仅 Δ；组旋转 Δ+N个 | **9/9** |
| 回归 | studio v0.3 / v0.4 / v0.5 三套 E2E | **14/14 · 16/16 · 7/7** |
| 真实 VLM 探针（scripts/probe_spec_rotate.py） | 合成图（矩形 15° + 斜排文字 12°）→ POST /api/spec → glm-5.3-flash 对两元素均输出 rotate=10（±8° 容差内），normalize 透传，门 0 通过 | **✅** |
| 四道门闭环 | 探针返回 spec 直送 /api/build → report ok=true, gates=4, failures=[]，PDF+PPTX 产出 | **✅** |

> 注：VLM 角度估计存在个体差异（本例 15°/12° 均报 10°，在 ±8° 容差内），
> 抽取后可在 studio 旋转手柄/属性面板微调 —— 识别→编辑→校验正是本全链路的设计闭环。
