# 一级芯界 AI Farm OS

智能农场作业操作系统。中文界面，决策优先、地图为中心。本仓库是 **Unified Mainline**：Vite + React + TypeScript 前端，FastAPI 后端，默认 SQLite。

PowerShell Demo 只作为产品与交互参考，没有复制其技术栈。

## 一条命令启动（无需 Docker）

```bash
chmod +x scripts/*.sh
./scripts/dev.sh
```

等价：`npm start`。脚本会先拉起 API，等到 `/api/health` 通过后再开前端；退出前端时停 API。

- 前端：http://127.0.0.1:5173
- API：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/health

分终端启动：

```bash
./scripts/start-api.sh   # 终端 1
./scripts/start-web.sh   # 终端 2
```

默认不设置 `DATABASE_URL` 时使用 `apps/api/data/farm.db`。首次启动若库为空会写入怀柔示范农场种子数据。

可选 PostgreSQL：

```bash
export DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/farm"
```

## 构建与测试

```bash
python3 -m pip install -r apps/api/requirements.txt -r requirements-dev.txt
npm --prefix apps/web install
python3 -m compileall apps/api/app
python3 -m pytest
npm --prefix apps/web test
npm run build
```

或：`npm run check`（compileall + pytest + 前端单测 + 生产构建）。

## 数据诚实性

凡涉及传感、机器人、设备控制的能力都带 `data_source`：

| 值 | 含义 |
| --- | --- |
| `REAL` | 真实接入（本演示场暂无） |
| `SIMULATION` | 仿真回放或顾问假设 |
| `MANUAL` | 人工台账 / 抄表 |

灌溉建议按仿真墒情阈值与 ET₀×Kc 计算，**采纳只生成任务**，不开阀。系统不会伪造实时传感器、机器人 GPS，也不会让 AI 直接控制机身。机器人指令接口固定返回 409。

示范场情景时钟固定为 `2026-09-13 08:30`，便于建议、逾期与演示可复现。

## 模块

- **P0** 决策看板、数字孪生（墒情/作物/风险/设备/传感器）、资产、作物、水肥、任务
- **P1** 设备、AI 智能体、诊断、AI 中心
- **P2** 机器人（stub）、车队、采后
- **P3** 供应商、协作、架构页
- **演示辅助** 工作台、本季与历史

详见 [ROADMAP.md](ROADMAP.md) 与 [OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)。
