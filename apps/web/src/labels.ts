import type { DataSource, DecisionUrgency, RiskLevel, TaskPriority, TaskStatus } from "./types";

export const DATA_SOURCE_LABEL: Record<DataSource, string> = {
  REAL: "REAL 真实",
  SIMULATION: "SIMULATION 仿真",
  MANUAL: "MANUAL 台账",
};

export const TASK_STATUS_LABEL: Record<TaskStatus, string> = {
  todo: "待办",
  in_progress: "进行中",
  done: "已完成",
  cancelled: "已取消",
};

export const TASK_PRIORITY_LABEL: Record<TaskPriority, string> = {
  low: "低",
  normal: "普通",
  high: "高",
  urgent: "紧急",
};

export const TASK_ORIGIN_LABEL: Record<string, string> = {
  manual: "人工登记",
  ai_suggested: "顾问建议",
};

export const RISK_LABEL: Record<RiskLevel, string> = {
  low: "低风险",
  medium: "中风险",
  high: "高风险",
};

export const URGENCY_LABEL: Record<DecisionUrgency, string> = {
  urgent: "立即拍板",
  high: "今日处理",
  normal: "可排期",
};

export const HEALTH_LABEL: Record<string, string> = {
  healthy: "正常",
  watch: "观察",
  stress: "水分胁迫",
  risk: "植保风险",
};

export const ASSET_STATUS_LABEL: Record<string, string> = {
  in_service: "在用",
  maintenance: "检修",
  retired: "停用",
};

export const MOISTURE_STATUS_LABEL: Record<string, string> = {
  dry: "偏干",
  ok: "适宜",
  wet: "偏湿",
  na: "无墒情",
};

export const KIND_LABEL: Record<string, string> = {
  irrigation: "水肥",
  climate: "棚室",
  harvest: "采收",
  diagnosis: "诊断",
  task: "任务",
};

export function labelOf(map: Record<string, string>, key: string | null | undefined): string {
  if (!key) return "—";
  return map[key] ?? key;
}
