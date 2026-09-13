# 一级芯界 AI Farm OS

智能农场作业操作系统。中文界面，决策优先、地图为中心。本仓库是 **Unified Mainline**：Vite + React + TypeScript 前端，FastAPI 后端，默认 SQLite。

PowerShell Demo 只作为产品与交互参考，没有复制其技术栈。

## 本地启动（无需 Docker）

默认不设置 `DATABASE_URL` 时使用 `apps/api/data/farm.db`。首次启动若库为空会写入怀柔示范农场种子数据。

```bash
# 终端 1
chmod +x scripts/*.sh
./scripts/start-api.sh

# 终端 2
./scripts/start-web.sh
```

或一条命令（前台为前端，退出时停 API）：

```bash
./scripts/dev.sh
```

- 前端：http://127.0.0.1:5173
- API：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/health

可选 PostgreSQL：

```bash
export DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/farm"
```

## 构建检查

```bash
python3 -m compileall apps/api/app
npm --prefix apps/web install
npm run build
```

## 数据诚实性

凡涉及传感、机器人、设备控制的能力都带 `data_source`：

| 值 | 含义 |
| --- | --- |
| `REAL` | 真实接入（本演示场暂无） |
| `SIMULATION` | 仿真回放或顾问假设 |
| `MANUAL` | 人工台账 / 抄表 |

系统不会伪造实时传感器、机器人 GPS，也不会让 AI 直接控制机身。机器人指令接口固定返回 409。

## 模块

- **P0** 决策看板、数字孪生（墒情/作物/风险/设备/传感器）、资产、作物、水肥、任务
- **P1** 设备、AI 智能体、诊断、AI 中心
- **P2** 机器人（stub）、车队、采后
- **P3** 供应商、协作、架构页
- **演示辅助** 工作台、本季与历史

详见 [ROADMAP.md](ROADMAP.md) 与 [OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)。
