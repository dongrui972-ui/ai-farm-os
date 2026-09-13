import { useState } from "react";
import { api } from "../api";
import { DataSourceBadge, ErrorText, Loading, PageHeader } from "../components/Ui";
import { useLoad } from "../hooks";
import type { AgentRun } from "../types";

export function AgentsPage() {
  const { data, error, reload } = useLoad(() => api.agents());
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [name, setName] = useState("");
  if (error) return <ErrorText error={error} />;
  if (!data) return <Loading />;
  return (
    <>
      <PageHeader
        title="AI 智能体"
        subtitle="顾问只产出建议。controls_hardware 恒为 false，不会开阀、喷药或调度机器人。"
      />
      <div className="grid two">
        <section className="card">
          {data.map((agent) => (
            <article key={agent.id} className="card" style={{ marginBottom: 10 }}>
              <div className="row-actions" style={{ justifyContent: "space-between" }}>
                <h3>
                  {agent.name} · {agent.role}
                </h3>
                <DataSourceBadge source={agent.data_source} />
              </div>
              <p className="muted">{agent.description}</p>
              <p className="muted">上次仿真运行 {agent.last_run_at ?? "—"} · 控制硬件：否</p>
              <div className="row-actions">
                <button
                  className="btn ghost"
                  onClick={() => void api.agent(agent.id).then((d) => {
                    setRuns(d.runs ?? []);
                    setName(d.name);
                  })}
                >
                  查看运行
                </button>
                <button
                  className="btn"
                  onClick={() =>
                    void api.runAgent(agent.id).then((run) => {
                      setRuns((prev) => [run, ...prev]);
                      setName(agent.name);
                      reload();
                    })
                  }
                >
                  仿真重跑
                </button>
              </div>
            </article>
          ))}
        </section>
        <section className="card">
          <h2>{name || "运行记录"}</h2>
          {runs.length === 0 ? <p className="muted">选择智能体。</p> : null}
          {runs.map((run) => (
            <article key={run.id} className="card" style={{ marginBottom: 8 }}>
              <strong>{run.created_at}</strong>
              <p>{run.summary}</p>
              <p className="muted">{run.recommendation}</p>
              <DataSourceBadge source={run.data_source} />
            </article>
          ))}
        </section>
      </div>
    </>
  );
}
