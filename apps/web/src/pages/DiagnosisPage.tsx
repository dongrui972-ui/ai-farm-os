import { useState } from "react";
import { api } from "../api";
import { DataPageState } from "../components/PageState";
import { DataSourceBadge, PageHeader, RiskBadge } from "../components/Ui";
import { useLoad } from "../hooks";

export function DiagnosisPage() {
  const { data, error, reload } = useLoad(() => api.diagnoses());
  const [title, setTitle] = useState("");
  const [symptom, setSymptom] = useState("");
  return (
    <DataPageState data={data} error={error}>
      {(rows) => (
        <>
          <PageHeader
            title="诊断"
            subtitle="仿真鉴别只是假设。须人工镜检后决策。系统不喷药、不联动植保机。"
          />
          <section className="card form" style={{ marginBottom: 14 }}>
            <strong>人工登记一条田间观察</strong>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="标题" />
            <textarea value={symptom} onChange={(e) => setSymptom(e.target.value)} placeholder="症状与取样说明" rows={3} />
            <button
              className="btn"
              disabled={!title || !symptom}
              onClick={() =>
                void api
                  .createDiagnosis({ title, symptom, conclusion: "待农技员确认", data_source: "MANUAL", confidence: 0 })
                  .then(() => {
                    setTitle("");
                    setSymptom("");
                    reload();
                  })
              }
            >
              写入台账
            </button>
          </section>
          <div className="grid cards">
            {rows.map((item) => (
              <article className="card" key={item.id}>
                <div className="row-actions" style={{ justifyContent: "space-between" }}>
                  <h3>{item.title}</h3>
                  <RiskBadge level={item.severity} />
                </div>
                <p>{item.symptom}</p>
                <p className="muted">{item.conclusion}</p>
                <p className="muted">
                  {item.zone_code} · 置信度 {item.confidence} · {item.created_at}
                </p>
                <DataSourceBadge source={item.data_source} />
              </article>
            ))}
          </div>
        </>
      )}
    </DataPageState>
  );
}
