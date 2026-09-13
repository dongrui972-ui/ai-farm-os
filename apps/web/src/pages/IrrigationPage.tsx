import { useState } from "react";
import { api } from "../api";
import { DataSourceBadge, ErrorText, Loading, PageHeader, StatusBadge } from "../components/Ui";
import { useLoad } from "../hooks";

export function IrrigationPage() {
  const { data, error, reload } = useLoad(() => api.irrigation());
  const [message, setMessage] = useState("");
  if (error) return <ErrorText error={error} />;
  if (!data) return <Loading />;

  async function accept(id: string) {
    const result = await api.acceptIrrigation(id);
    setMessage(`${result.note} 任务 ${result.task.id}`);
    reload();
  }

  return (
    <>
      <PageHeader
        title="水肥灌溉"
        subtitle="回路台账与仿真建议。采纳建议只会生成人工任务，不会远程开阀或启泵。"
      />
      <div className="callout">所有回路 control_enabled = false。水压与阀门需现场确认。</div>
      {message ? <p className="muted">{message}</p> : null}
      <section className="card" style={{ marginTop: 12 }}>
        <table>
          <thead>
            <tr>
              <th>回路</th>
              <th>墒情</th>
              <th>窗口 / 定额</th>
              <th>建议</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {data.map((item) => (
              <tr key={item.id}>
                <td>
                  {item.zone_code} {item.name}
                  <div className="muted">
                    {item.valve_code} · {item.method} <StatusBadge>{item.status}</StatusBadge>
                  </div>
                </td>
                <td>{item.moisture_pct == null ? "—" : `${item.moisture_pct}%`}</td>
                <td>
                  {item.next_window}
                  <div className="muted">
                    {item.used_m3}/{item.budget_m3} m³
                  </div>
                </td>
                <td>
                  {item.recommendation}
                  <div>
                    <DataSourceBadge source={item.data_source} />
                  </div>
                </td>
                <td>
                  {item.recommendation_mm ? (
                    <button className="btn" onClick={() => void accept(item.id)}>
                      采纳为任务
                    </button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
