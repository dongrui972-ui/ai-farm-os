import type { ComponentType } from "react";

import { AICenterPage } from "./pages/AICenterPage";
import { AgentsPage } from "./pages/AgentsPage";
import { ArchitecturePage } from "./pages/ArchitecturePage";
import { AssetsPage } from "./pages/AssetsPage";
import { CollaborationPage } from "./pages/CollaborationPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DevicesPage } from "./pages/DevicesPage";
import { DiagnosisPage } from "./pages/DiagnosisPage";
import { FleetPage } from "./pages/FleetPage";
import { IrrigationPage } from "./pages/IrrigationPage";
import { PlantsPage } from "./pages/PlantsPage";
import { PostHarvestPage } from "./pages/PostHarvestPage";
import { RobotsPage } from "./pages/RobotsPage";
import { SeasonsPage } from "./pages/SeasonsPage";
import { TasksPage } from "./pages/TasksPage";
import { TwinPage } from "./pages/TwinPage";
import { VendorsPage } from "./pages/VendorsPage";
import { WorkbenchPage } from "./pages/WorkbenchPage";

export type RouteGroupId = "command" | "p0" | "p1" | "p2" | "p3";

export type AppRouteItem = {
  path: string;
  label: string;
  group: RouteGroupId;
  component: ComponentType;
  stub?: boolean;
};

const ROUTE_GROUPS_META: Record<RouteGroupId, { title: string }> = {
  command: { title: "指挥" },
  p0: { title: "生产 P0" },
  p1: { title: "感知与智能 P1" },
  p2: { title: "装备与物流 P2" },
  p3: { title: "协同与体系 P3" },
};

export const APP_ROUTES: AppRouteItem[] = [
  { path: "/dashboard", label: "决策看板", group: "command", component: DashboardPage },
  { path: "/twin", label: "数字孪生", group: "command", component: TwinPage },
  { path: "/workbench", label: "工作台", group: "command", component: WorkbenchPage },
  { path: "/seasons", label: "本季与历史", group: "command", component: SeasonsPage },
  { path: "/assets", label: "资产", group: "p0", component: AssetsPage },
  { path: "/plants", label: "作物", group: "p0", component: PlantsPage },
  { path: "/irrigation", label: "水肥灌溉", group: "p0", component: IrrigationPage },
  { path: "/tasks", label: "任务", group: "p0", component: TasksPage },
  { path: "/devices", label: "设备", group: "p1", component: DevicesPage },
  { path: "/agents", label: "AI 智能体", group: "p1", component: AgentsPage },
  { path: "/diagnosis", label: "诊断", group: "p1", component: DiagnosisPage },
  { path: "/ai-center", label: "AI 中心", group: "p1", component: AICenterPage },
  { path: "/robots", label: "机器人", group: "p2", component: RobotsPage, stub: true },
  { path: "/fleet", label: "车队", group: "p2", component: FleetPage },
  { path: "/postharvest", label: "采后", group: "p2", component: PostHarvestPage },
  { path: "/vendors", label: "供应商", group: "p3", component: VendorsPage },
  { path: "/collaboration", label: "协作", group: "p3", component: CollaborationPage },
  { path: "/architecture", label: "系统架构", group: "p3", component: ArchitecturePage },
];

export const APP_NAV_GROUPS = (Object.keys(ROUTE_GROUPS_META) as RouteGroupId[]).map((id) => ({
  id,
  title: ROUTE_GROUPS_META[id].title,
  items: APP_ROUTES.filter((route) => route.group === id),
}));
