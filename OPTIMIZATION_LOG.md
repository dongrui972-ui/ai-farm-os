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
