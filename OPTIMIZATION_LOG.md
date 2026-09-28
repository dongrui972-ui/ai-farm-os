# 优化与边界日志

记录 Unified Mainline 里「有意做成 stub / 仿真」的位置，避免后续把演示数据误当成现场能力。

## 数据源

- 模型与 API 统一字段 `data_source: REAL | SIMULATION | MANUAL`。
- 种子农场「一级芯界怀柔示范农场」：作物、资产、任务、供应商、协作、冷库抄表为 `MANUAL`。
- 墒情分区值、灌溉建议、智能体运行、诊断假设、AI 作业为 `SIMULATION`。
- 当前种子中 **没有** `REAL` 传感或机身。

## Stub / 拒绝控制

| 能力 | 行为 |
| --- | --- |
| 机器人位姿 | `last_pose = null`，前端不画轨迹 |
| `POST /api/robots/{id}/command` | HTTP 409 `robot_unbound` |
| 灌溉采纳 | 只创建任务，不开阀 |
| 智能体 / AI 作业 | `controls_hardware = false` |
| 设备状态 | `sim_online` / `unbound` / `manual`，不用「在线」冒充现场 |
| 气象站 / 摄像头 / 阀遥测 | `unbound`，无推流 |

## 产品选择

- 看板先列「今日需拍板」，而不是先堆图表。
- 孪生默认墒情层，可切五层。
- 中文 UI，侧栏按 P0–P3 分组，机器人标注 STUB。
- 未引入 IoT 中间件或机器人 SDK，避免半真半假的集成层。

## 已知限制

- 单农场 SQLite，无多租户。
- 无登录鉴权（演示 OS）。
- 仿真读数为种子回放，不会随墙钟自动增长。
- 前端地图为 SVG 示意，未接 GIS。

## 2026-09 Refactor & Hardening 记录

### 分层重构

- 路由拆薄：`routers/*` 仅保留 HTTP 层职责。
- 新增 `services/*`：把看板聚合、台账写入、智能体重跑、stub 拒绝逻辑下沉到服务层。
- 新增 `schemas/*`：创建/更新类接口统一请求模型，避免在路由里散落内联 BaseModel。

### 共享类型与去重

- 引入共享请求类型：`DataSourceLiteral`、任务状态/优先级、风险等级。
- 提取 `DATA_SOURCE_LEGEND`、`HONESTY_BOUNDARIES`、孪生图层定义为常量，消除重复硬编码。
- Seed 数据增加 `_season / _zone / _task / _robot` 构造器，减少重复样板并明确 demo 语义。

### 前端结构优化

- 路由与侧栏统一注册表（`appRoutes.ts`），避免导航配置与 `<Route>` 重复维护。
- API 调用统一 `ApiClient`，写操作输入从 `Partial<T>` 改为显式 DTO 类型，防止误传字段。
- 新增 `DataPageState`，统一加载与错误呈现，减少页面重复样板。

### 冒烟与可信边界

- 新增 `apps/api/smoke_routes.py` 覆盖 P0–P3 关键 GET/POST/PATCH。
- 冒烟脚本强制校验：
  - `/api/robots/{id}/command` 必须 409（拒绝伪控制）
  - `/api/irrigation/{id}/accept-recommendation` 仅创建任务，不下发阀控
  - 关键对象 `data_source` 仅允许 `REAL|SIMULATION|MANUAL`

## 2026-09 农艺深度（本轮）

### 为什么做

P0 页面在重构后结构干净，但决策仍是静态种子文案：看板截断 6 条、灌溉建议不解释「为何 12mm」、作物页只有生育期字符串。要让示范场像作业 OS，必须把墒情、ET 和生育期连成可复核的建议，同时继续拒绝伪实时控制。

### 农艺模型（全部 SIMULATION）

- 新增 `services/agronomy.py`：FAO-56 风格管理层水量平衡。
  - ET₀ 取怀柔 9 月中旬情景表（3.6 mm），温室乘 0.78；**不是气象站**。
  - 作物×生育期给出 Kc 与 MAD，灌水阈值 = 田间持水量 − RAW。
  - 跌破阈值时给滴灌/喷灌单次脉冲（滴灌上限 12mm，湿润比 0.25 折算 m³），不一次灌到田间持水量。
  - 生菜采收期强制停水；黄瓜棚湿风险「缩短 + 通风」。
- `/api/dashboard`、`/api/irrigation`、`/api/plants`、`/api/twin`、`/api/agronomy` 都挂同一套建议。
- `POST /irrigation/{id}/accept-recommendation` 仍只写任务；响应带 `agronomy.control_enabled = false`。
- 示范场情景时钟冻结 `2026-09-13 08:30`，逾期判定不再写死另一时间。

### 测试与 DX

- `tests/` pytest：路由冒烟、农艺单测、机器人 409、灌溉采纳不控阀、种子无 REAL。
- `apps/api/smoke_routes.py` 改为转调 pytest，保持旧命令可用。
- 前端 Vitest 覆盖中文标签、路由表、墒情着色。
- `./scripts/dev.sh` 等待 `/api/health` 后开 Vite。

### UX

- 决策卡展示依据列表与作业窗口。
- 灌溉/作物改为卡片，能看阈值、Kc、ETc。
- 孪生侧栏解释该层含义 + 分区农艺。
- 任务筛选、中文状态、空态、错误重试。
- 提高对比度与按钮最小高度，窄屏用「打开菜单」。

