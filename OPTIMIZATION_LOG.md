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
