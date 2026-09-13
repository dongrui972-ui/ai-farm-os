import { useState } from "react";
import { api } from "../api";
import { DataPageState } from "../components/PageState";
import { DataSourceBadge, PageHeader, StatusBadge } from "../components/Ui";
import { useLoad } from "../hooks";

export function TasksPage() {
  const { data, error, reload } = useLoad(() => api.tasks());
  const [title, setTitle] = useState("");

  return (
    <DataPageState data={data} error={error}>
      {(rows) => (
        <>
          <PageHeader title="任务" subtitle="人工执行队列。AI 建议任务仍需人确认，状态变更写回 SQLite。" />
          <section className="card form" style={{ marginBottom: 14 }}>
            <strong>新建台账任务</strong>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="任务标题" />
            <button
              className="btn"
              disabled={!title}
              onClick={() => {
                void api.createTask({ title, task_type: "general", assignee: "值班", data_source: "MANUAL" }).then(() => {
                  setTitle("");
                  reload();
                });
              }}
            >
              登记
            </button>
          </section>
          <section className="card">
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
                        {item.zone_code} · {item.origin} <DataSourceBadge source={item.data_source} />
                      </div>
                    </td>
                    <td>{item.priority}</td>
                    <td>{item.assignee}</td>
                    <td>{item.due_at}</td>
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
          </section>
        </>
      )}
    </DataPageState>
  );
}
