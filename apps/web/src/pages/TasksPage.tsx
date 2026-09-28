import { useMemo, useState } from "react";
import { api } from "../api";
import { DataPageState } from "../components/PageState";
import { DataSourceBadge, EmptyState, PageHeader, StatusBadge } from "../components/Ui";
import { useLoad } from "../hooks";
import { TASK_ORIGIN_LABEL, TASK_PRIORITY_LABEL, TASK_STATUS_LABEL, labelOf } from "../labels";
import type { TaskStatus } from "../types";

const FILTERS: { id: "open" | "all" | TaskStatus; label: string }[] = [
  { id: "open", label: "未关闭" },
  { id: "all", label: "全部" },
  { id: "todo", label: "待办" },
  { id: "in_progress", label: "进行中" },
  { id: "done", label: "已完成" },
];

export function TasksPage() {
  const { data, error, reload } = useLoad(() => api.tasks());
  const [title, setTitle] = useState("");
  const [filter, setFilter] = useState<(typeof FILTERS)[number]["id"]>("open");

  const rows = useMemo(() => {
    const list = data ?? [];
    if (filter === "all") return list;
    if (filter === "open") return list.filter((item) => item.status === "todo" || item.status === "in_progress");
    return list.filter((item) => item.status === filter);
  }, [data, filter]);

  return (
    <DataPageState data={data} error={error} onRetry={reload}>
      {() => (
        <>
          <PageHeader title="任务" subtitle="人工执行队列。顾问建议的补灌任务仍需人确认后才算拍板，状态写回 SQLite，不驱动阀控。" />
          <section className="card form" style={{ marginBottom: 14 }}>
            <strong>新建台账任务</strong>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="任务标题，例如：A4 冲肥复核" />
            <button
              className="btn"
              disabled={!title.trim()}
              onClick={() => {
                void api.createTask({ title: title.trim(), task_type: "general", assignee: "值班", data_source: "MANUAL" }).then(() => {
                  setTitle("");
                  reload();
                });
              }}
            >
              登记
            </button>
          </section>
          <div className="layer-bar">
            {FILTERS.map((item) => (
              <button key={item.id} className={filter === item.id ? "on" : ""} onClick={() => setFilter(item.id)}>
                {item.label}
              </button>
            ))}
          </div>
          <section className="card">
            {rows.length === 0 ? (
              <EmptyState title="这个筛选下没有任务" hint="试试「全部」，或从水肥页采纳一条建议。" />
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>任务</th>
                      <th>优先级</th>
                      <th>责任人</th>
                      <th>截止</th>
                      <th>状态</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((item) => (
                      <tr key={item.id}>
                        <td>
                          {item.title}
                          <div className="muted">
                            {item.zone_code ?? "场级"} · {labelOf(TASK_ORIGIN_LABEL, item.origin)}{" "}
                            <DataSourceBadge source={item.data_source} />
                          </div>
                          {item.notes ? <div className="muted clamp">{item.notes}</div> : null}
                        </td>
                        <td>{labelOf(TASK_PRIORITY_LABEL, item.priority)}</td>
                        <td>{item.assignee || "—"}</td>
                        <td>{item.due_at ?? "—"}</td>
                        <td>
                          <StatusBadge>{item.status}</StatusBadge>
                        </td>
                        <td>
                          {item.status !== "done" ? (
                            <button className="btn ghost" onClick={() => void api.patchTask(item.id, { status: "done" }).then(reload)}>
                              完成
                            </button>
                          ) : null}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
          <p className="muted" style={{ marginTop: 8 }}>
            当前筛选 {rows.length} / 全部 {data?.length ?? 0} 条。{labelOf(TASK_STATUS_LABEL, "todo")} 与进行中计入看板未关闭数。
          </p>
        </>
      )}
    </DataPageState>
  );
}
