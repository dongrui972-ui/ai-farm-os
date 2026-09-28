import { api } from "../api";
import { DataPageState } from "../components/PageState";
import { DataSourceBadge, EmptyState, PageHeader, RiskBadge, StatusBadge } from "../components/Ui";
import { useLoad } from "../hooks";
import { MOISTURE_STATUS_LABEL, labelOf } from "../labels";

export function PlantsPage() {
  const { data, error, reload } = useLoad(() => api.plants());
  return (
    <DataPageState data={data} error={error} onRetry={reload}>
      {(rows) => (
        <>
          <PageHeader
            title="作物"
            subtitle="生育期来自农技员台账。水肥与巡查建议随生育期 Kc / MAD 变化，分区墒情仅为仿真对照。"
          />
          {rows.length === 0 ? (
            <EmptyState title="本季没有在田作物" hint="切换茬口或补登台账后再查看。" />
          ) : (
            <div className="stack">
              {rows.map((item) => {
                const agronomy = item.agronomy;
                return (
                  <article className="card" key={item.id}>
                    <div className="row-actions" style={{ justifyContent: "space-between" }}>
                      <div>
                        <h3>
                          {item.zone_code} {item.crop_name} · {item.variety}
                        </h3>
                        <p className="muted">
                          {item.planted_at} → {item.expected_harvest ?? "未排产"} · 生育期 {item.growth_stage}
                        </p>
                      </div>
                      <div className="row-actions">
                        <StatusBadge>{item.health_status}</StatusBadge>
                        {item.risk_level ? <RiskBadge level={item.risk_level} /> : null}
                        <DataSourceBadge source={item.data_source} />
                      </div>
                    </div>
                    <div className="grid three compact">
                      <div>
                        <div className="label">墒情对照</div>
                        <strong>{item.moisture_pct == null ? "—" : `${item.moisture_pct}%`}</strong>
                        <div className="muted">
                          阈值 {agronomy?.threshold_pct ?? "—"}% · {labelOf(MOISTURE_STATUS_LABEL, agronomy?.moisture_status)}
                        </div>
                      </div>
                      <div>
                        <div className="label">阶段需水</div>
                        <strong>
                          Kc {agronomy?.kc ?? "—"} · ETc {agronomy?.etc_mm ?? "—"} mm
                        </strong>
                        <div className="muted">{agronomy?.action_label}</div>
                      </div>
                      <div>
                        <div className="label">顾问结论</div>
                        <strong>{agronomy?.summary ?? "—"}</strong>
                        <div className="muted">{agronomy?.window_hint}</div>
                      </div>
                    </div>
                    {item.notes ? <p>{item.notes}</p> : null}
                    {agronomy?.care?.length ? (
                      <div>
                        <div className="label">生育期要点</div>
                        <ul className="why-list">
                          {agronomy.care.map((line) => (
                            <li key={line}>{line}</li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                    {agronomy?.watch?.length ? <p className="muted">关注：{agronomy.watch.join("、")}</p> : null}
                  </article>
                );
              })}
            </div>
          )}
        </>
      )}
    </DataPageState>
  );
}
