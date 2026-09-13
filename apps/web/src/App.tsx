import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { useLoad } from "./hooks";
import { api } from "./api";
import { DataSourceBadge } from "./components/Ui";
import { DashboardPage } from "./pages/DashboardPage";
import { TwinPage } from "./pages/TwinPage";
import { AssetsPage } from "./pages/AssetsPage";
import { PlantsPage } from "./pages/PlantsPage";
import { IrrigationPage } from "./pages/IrrigationPage";
import { TasksPage } from "./pages/TasksPage";
import { DevicesPage } from "./pages/DevicesPage";
import { AgentsPage } from "./pages/AgentsPage";
import { DiagnosisPage } from "./pages/DiagnosisPage";
import { AICenterPage } from "./pages/AICenterPage";
import { RobotsPage } from "./pages/RobotsPage";
import { FleetPage } from "./pages/FleetPage";
import { PostHarvestPage } from "./pages/PostHarvestPage";
import { VendorsPage } from "./pages/VendorsPage";
import { CollaborationPage } from "./pages/CollaborationPage";
import { ArchitecturePage } from "./pages/ArchitecturePage";
import { WorkbenchPage } from "./pages/WorkbenchPage";
import { SeasonsPage } from "./pages/SeasonsPage";

const NAV = [
  {
    title: "指挥",
    items: [
      { to: "/dashboard", label: "决策看板" },
      { to: "/twin", label: "数字孪生" },
      { to: "/workbench", label: "工作台" },
      { to: "/seasons", label: "本季与历史" },
    ],
  },
  {
    title: "生产 P0",
    items: [
      { to: "/assets", label: "资产" },
      { to: "/plants", label: "作物" },
      { to: "/irrigation", label: "水肥灌溉" },
      { to: "/tasks", label: "任务" },
    ],
  },
  {
    title: "感知与智能 P1",
    items: [
      { to: "/devices", label: "设备" },
      { to: "/agents", label: "AI 智能体" },
      { to: "/diagnosis", label: "诊断" },
      { to: "/ai-center", label: "AI 中心" },
    ],
  },
  {
    title: "装备与物流 P2",
    items: [
      { to: "/robots", label: "机器人", stub: true },
      { to: "/fleet", label: "车队" },
      { to: "/postharvest", label: "采后" },
    ],
  },
  {
    title: "协同与体系 P3",
    items: [
      { to: "/vendors", label: "供应商" },
      { to: "/collaboration", label: "协作" },
      { to: "/architecture", label: "系统架构" },
    ],
  },
];

export default function App() {
  const { data: meta } = useLoad(() => api.meta());

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <small>YIJI XINJIE</small>
          <strong>一级芯界</strong>
          <div className="muted" style={{ color: "#9bb5aa", marginTop: 4 }}>
            AI Farm OS
          </div>
        </div>
        {NAV.map((group) => (
          <nav key={group.title} className="nav-group">
            <h4>{group.title}</h4>
            {group.items.map((item) => (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? "active" : "")}>
                {item.label}
                {"stub" in item && item.stub ? <span className="stub">STUB</span> : null}
              </NavLink>
            ))}
          </nav>
        ))}
      </aside>
      <div className="main">
        <div className="topbar">
          <div>
            <strong>{meta?.farm?.name ?? "一级芯界示范农场"}</strong>
            <div className="farm-meta">
              {meta?.farm?.location} · {meta?.season?.name ?? "本季"} · {meta?.line}
            </div>
          </div>
          <div className="legend">
            <DataSourceBadge source="REAL" />
            <DataSourceBadge source="SIMULATION" />
            <DataSourceBadge source="MANUAL" />
          </div>
        </div>
        <div className="content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/twin" element={<TwinPage />} />
            <Route path="/workbench" element={<WorkbenchPage />} />
            <Route path="/seasons" element={<SeasonsPage />} />
            <Route path="/assets" element={<AssetsPage />} />
            <Route path="/plants" element={<PlantsPage />} />
            <Route path="/irrigation" element={<IrrigationPage />} />
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/devices" element={<DevicesPage />} />
            <Route path="/agents" element={<AgentsPage />} />
            <Route path="/diagnosis" element={<DiagnosisPage />} />
            <Route path="/ai-center" element={<AICenterPage />} />
            <Route path="/robots" element={<RobotsPage />} />
            <Route path="/fleet" element={<FleetPage />} />
            <Route path="/postharvest" element={<PostHarvestPage />} />
            <Route path="/vendors" element={<VendorsPage />} />
            <Route path="/collaboration" element={<CollaborationPage />} />
            <Route path="/architecture" element={<ArchitecturePage />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}
