import type { DataSource } from "../types";

const SOURCE_LABEL: Record<DataSource, string> = {
  REAL: "REAL 真实",
  SIMULATION: "SIMULATION 仿真",
  MANUAL: "MANUAL 台账",
};

export function DataSourceBadge({ source }: { source: DataSource }) {
  return <span className={`badge ${source}`}>{SOURCE_LABEL[source] ?? source}</span>;
}

export function RiskBadge({ level }: { level: string }) {
  const label = level === "high" ? "高风险" : level === "medium" ? "中风险" : "低风险";
  return <span className={`badge risk-${level}`}>{label}</span>;
}

export function StatusBadge({ children }: { children: string }) {
  return <span className="badge status">{children}</span>;
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
  return <p className="muted">加载中…</p>;
}

export function ErrorText({ error }: { error: string }) {
  return <p className="error">{error}</p>;
}
