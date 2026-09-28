import type { DataSource } from "../types";
import { ASSET_STATUS_LABEL, CIRCUIT_STATUS_LABEL, DATA_SOURCE_LABEL, HEALTH_LABEL, RISK_LABEL, ROBOT_STATUS_LABEL, TASK_STATUS_LABEL, labelOf } from "../labels";

export function DataSourceBadge({ source }: { source: DataSource }) {
  return <span className={`badge ${source}`}>{DATA_SOURCE_LABEL[source] ?? source}</span>;
}

export function RiskBadge({ level }: { level: string }) {
  return <span className={`badge risk-${level}`}>{labelOf(RISK_LABEL, level)}</span>;
}

export function StatusBadge({ children }: { children: string }) {
  const label = labelOf(
    { ...TASK_STATUS_LABEL, ...HEALTH_LABEL, ...ASSET_STATUS_LABEL, ...CIRCUIT_STATUS_LABEL, ...ROBOT_STATUS_LABEL },
    children,
  );
  return <span className="badge status">{label}</span>;
}

export function PageHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <header className="page-head">
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </header>
  );
}

export function Loading() {
  return (
    <div className="empty-state" role="status">
      <strong>加载中</strong>
      <p className="muted">正在读取示范场台账与仿真建议…</p>
    </div>
  );
}

export function ErrorText({ error, onRetry }: { error: string; onRetry?: () => void }) {
  return (
    <div className="empty-state error-state" role="alert">
      <strong>无法加载本页</strong>
      <p className="muted">{error}</p>
      {onRetry ? (
        <button className="btn" onClick={onRetry}>
          重试
        </button>
      ) : null}
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint: string }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      <p className="muted">{hint}</p>
    </div>
  );
}
