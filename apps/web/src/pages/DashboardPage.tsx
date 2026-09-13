import { Link } from "react-router-dom";
import { api } from "../api";
import { FarmMap } from "../components/FarmMap";
import { DataSourceBadge, ErrorText, Loading, PageHeader, RiskBadge } from "../components/Ui";
import { useLoad } from "../hooks";

export function DashboardPage() {
  const { data, error } = useLoad(() => api.dashboard());
  const twin = useLoad(() => api.twin(["moisture", "risk"]));

  if (error) return <ErrorText error={error} />;
  if (!data) return <Loading />;

  return (
    <>
      <PageHeader
        title="今日需拍板"
        subtitle="决策优先，而不是仪表盘堆砌。建议来自仿真墒情、人工台账与农技复核，不会自动开阀或调度机身。"
      />
      <div className="grid kpi">
        {data.kpis.map((kpi) => (
          <article className="card" key={kpi.key}>
            <div className="value">{kpi.value}</div>
            <div className="label">{kpi.label}</div>
          </article>
        ))}
      </div>
      <div className="grid two" style={{ marginTop: 14 }}>
        <section className="card">
          <h2>决策队列</h2>
          {data.decisions.map((item) => (
            <article key={item.id} className={`card decision ${item.urgency}`}>
              <div className="row-actions" style={{ justifyContent: "space-between" }}>
                <h3>{item.title}</h3>
                <DataSourceBadge source={item.data_source} />
              </div>
              <p>{item.detail}</p>
              <Link className="btn" to={item.href}>
                {item.action_label}
              </Link>
            </article>
          ))}
        </section>
        <section className="card map-card">
          <h2>场区速览 · 墒情层</h2>
          {twin.data ? (
            <FarmMap zones={twin.data.zones} devices={twin.data.devices} layer="moisture" />
          ) : (
            <Loading />
          )}
          <p className="muted" style={{ marginTop: 8 }}>
            {twin.data?.disclaimer}
          </p>
        </section>
      </div>
      <div className="grid two" style={{ marginTop: 14 }}>
        <section className="card">
          <h2>风险分区</h2>
          <table>
            <thead>
              <tr>
                <th>分区</th>
                <th>风险</th>
                <th>说明</th>
              </tr>
            </thead>
            <tbody>
              {data.risk_zones.map((zone) => (
                <tr key={zone.id}>
                  <td>
                    {zone.code}
                    <div className="muted">{zone.name}</div>
                  </td>
                  <td>
                    <RiskBadge level={zone.risk_level} />
                  </td>
                  <td>{zone.risk_note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
        <section className="card">
          <h2>未关闭任务</h2>
          <table>
            <thead>
              <tr>
                <th>任务</th>
                <th>责任人</th>
                <th>截止</th>
              </tr>
            </thead>
            <tbody>
              {data.open_tasks.map((task) => (
                <tr key={task.id}>
                  <td>
                    {task.title}
                    <div className="muted">{task.zone_code}</div>
                  </td>
                  <td>{task.assignee}</td>
                  <td>{task.due_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </>
  );
}
