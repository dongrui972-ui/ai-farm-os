import { Link } from "react-router-dom";
import { api } from "../api";
import { DataPageState } from "../components/PageState";
import { FarmMap } from "../components/FarmMap";
import { DataSourceBadge, EmptyState, PageHeader, RiskBadge, StatusBadge } from "../components/Ui";
import { useLoad } from "../hooks";
import { KIND_LABEL, MOISTURE_STATUS_LABEL, TASK_PRIORITY_LABEL, URGENCY_LABEL, labelOf } from "../labels";

export function DashboardPage() {
  const { data, error, reload } = useLoad(() => api.dashboard());
  const twin = useLoad(() => api.twin(["moisture", "risk"]));

  return (
    <DataPageState data={data} error={error} onRetry={reload}>
      {(dashboard) => (
        <>
          <PageHeader
            title="今日需拍板"
            subtitle="先决策、后图表。补灌量来自仿真墒情阈值与 ET₀×Kc，作物台账为人工登记。系统不会自动开阀或调度机身。"
          />
          {dashboard.weather ? (
            <section className="weather-strip">
              <div>
                <strong>仿真气象</strong>
                <span>
                  {dashboard.weather.sky} · ET₀ {dashboard.weather.et0_mm} mm · {dashboard.weather.tmin_c}–{dashboard.weather.tmax_c}°C · 雨{" "}
                  {dashboard.weather.rain_mm} mm
                </span>
              </div>
              <DataSourceBadge source={dashboard.weather.data_source} />
              <p>{dashboard.weather.disclaimer}</p>
            </section>
          ) : null}
          <div className="grid kpi">
            {dashboard.kpis.map((kpi) => (
              <article className="card" key={kpi.key}>
                <div className="value">{kpi.value}</div>
                <div className="label">{kpi.label}</div>
              </article>
            ))}
          </div>
          <div className="grid two" style={{ marginTop: 14 }}>
            <section className="card">
              <h2>决策队列</h2>
              {dashboard.decisions.length === 0 ? (
                <EmptyState title="今日没有必须拍板的事项" hint="墒情、采收与逾期任务均在舒适区。可到工作台查看例行队列。" />
              ) : (
                dashboard.decisions.map((item) => (
                  <article key={item.id} className={`card decision ${item.urgency}`}>
                    <div className="row-actions" style={{ justifyContent: "space-between" }}>
                      <div>
                        <span className="badge status">{labelOf(KIND_LABEL, item.kind)}</span>{" "}
                        <span className="badge status">{labelOf(URGENCY_LABEL, item.urgency)}</span>
                      </div>
                      <DataSourceBadge source={item.data_source} />
                    </div>
                    <h3>{item.title}</h3>
                    <p>{item.detail}</p>
                    {item.why?.length ? (
                      <ul className="why-list">
                        {item.why.map((line) => (
                          <li key={line}>{line}</li>
                        ))}
                      </ul>
                    ) : null}
                    {item.window ? <p className="muted">窗口：{item.window}</p> : null}
                    <Link className="btn" to={item.href}>
                      {item.action_label}
                    </Link>
                  </article>
                ))
              )}
            </section>
            <section className="card map-card">
              <h2>场区速览 · 墒情相对阈值</h2>
              {twin.data ? (
                <FarmMap zones={twin.data.zones} devices={twin.data.devices} layer="moisture" />
              ) : twin.error ? (
                <p className="error">{twin.error}</p>
              ) : (
                <p className="muted">地图加载中…</p>
              )}
              <p className="muted" style={{ marginTop: 8 }}>
                {twin.data?.disclaimer}
              </p>
            </section>
          </div>
          <div className="grid two" style={{ marginTop: 14 }}>
            <section className="card">
              <h2>风险分区</h2>
              {dashboard.risk_zones.length === 0 ? (
                <EmptyState title="没有中高风险分区" hint="风险来自仿真水分胁迫与植保假设，不是自动处方。" />
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>分区</th>
                        <th>墒情 / 阈值</th>
                        <th>风险</th>
                        <th>说明</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboard.risk_zones.map((zone) => (
                        <tr key={zone.id}>
                          <td>
                            {zone.code}
                            <div className="muted">{zone.name}</div>
                          </td>
                          <td>
                            {zone.moisture_pct == null ? "—" : `${zone.moisture_pct}%`}
                            {zone.threshold_pct != null ? <div className="muted">阈值 {zone.threshold_pct}%</div> : null}
                            {zone.moisture_status ? (
                              <div className="muted">{labelOf(MOISTURE_STATUS_LABEL, zone.moisture_status)}</div>
                            ) : null}
                          </td>
                          <td>
                            <RiskBadge level={zone.risk_level} />
                            {zone.action_label ? <div className="muted">{zone.action_label}</div> : null}
                          </td>
                          <td>{zone.risk_note}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
            <section className="card">
              <h2>未关闭任务</h2>
              {dashboard.open_tasks.length === 0 ? (
                <EmptyState title="没有未关闭任务" hint="新的灌溉建议采纳后会进入本队列。" />
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>任务</th>
                        <th>优先级</th>
                        <th>责任人</th>
                        <th>截止</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboard.open_tasks.map((task) => (
                        <tr key={task.id}>
                          <td>
                            {task.title}
                            <div className="muted">{task.zone_code}</div>
                          </td>
                          <td>
                            <StatusBadge>{labelOf(TASK_PRIORITY_LABEL, task.priority)}</StatusBadge>
                          </td>
                          <td>{task.assignee}</td>
                          <td>{task.due_at}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </div>
          {dashboard.demo_clock_note ? <p className="muted">{dashboard.demo_clock_note}</p> : null}
        </>
      )}
    </DataPageState>
  );
}
