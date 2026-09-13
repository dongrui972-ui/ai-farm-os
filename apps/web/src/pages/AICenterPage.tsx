import { useState } from "react";
import { api } from "../api";
import { DataPageState } from "../components/PageState";
import { DataSourceBadge, PageHeader, StatusBadge } from "../components/Ui";
import { useLoad } from "../hooks";

export function AICenterPage() {
  const { data, error, reload } = useLoad(() => api.jobs());
  const [title, setTitle] = useState("");
  return (
    <DataPageState data={data} error={error}>
      {(rows) => (
        <>
          <PageHeader title="AI 中心" subtitle="纪要、风险扫描与计划任务。入队不会触发设备动作。" />
          <section className="card form" style={{ marginBottom: 14 }}>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="新作业标题" />
            <button
              className="btn"
              disabled={!title}
              onClick={() =>
                void api.createJob({ title, job_type: "briefing" }).then(() => {
                  setTitle("");
                  reload();
                })
              }
            >
              入队（仿真）
            </button>
          </section>
          <section className="card">
            <table>
              <thead>
                <tr>
                  <th>作业</th>
                  <th>类型</th>
                  <th>输出</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((job) => (
                  <tr key={job.id}>
                    <td>
                      {job.title}
                      <div className="muted">{job.created_at}</div>
                    </td>
                    <td>{job.job_type}</td>
                    <td>
                      {job.output_summary}
                      <div>
                        <DataSourceBadge source={job.data_source} />
                      </div>
                    </td>
                    <td>
                      <StatusBadge>{job.status}</StatusBadge>
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
