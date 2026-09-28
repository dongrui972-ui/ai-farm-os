import { useState } from "react";
import { api } from "../api";
import { DataPageState } from "../components/PageState";
import { DataSourceBadge, EmptyState, PageHeader, StatusBadge } from "../components/Ui";
import { useLoad } from "../hooks";
import { METHOD_LABEL, MOISTURE_STATUS_LABEL, labelOf } from "../labels";

export function IrrigationPage() {
  const { data, error, reload } = useLoad(() => api.irrigation());
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  async function accept(id: string) {
    setBusy(id);
    try {
      const result = await api.acceptIrrigation(id);
      setMessage(`${result.note} 已生成任务 ${result.task.id}`);
      reload();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "采纳失败");
    } finally {
      setBusy(null);
    }
  }

  return (
    <DataPageState data={data} error={error} onRetry={reload}>
      {(rows) => (
        <>
          <PageHeader
            title="水肥灌溉"
            subtitle="建议按仿真 0–20cm 墒情、作物 Kc 与 ET₀ 计算。点「采纳为任务」只写人工执行单，不会远程开阀或启泵。"
          />
          <div className="callout">所有回路 control_enabled = false。水压、过滤器与阀位必须现场确认。</div>
          {message ? <p className="callout">{message}</p> : null}
          <section className="card" style={{ marginTop: 12 }}>
            {rows.length === 0 ? (
              <EmptyState title="没有灌溉回路" hint="种子场应包含温室滴灌与露地喷灌。请检查数据库是否已写入。" />
            ) : (
              <div className="stack">
                {rows.map((item) => {
                  const agronomy = item.agronomy;
                  return (
                    <article className="card irrig-card" key={item.id}>
                      <div className="row-actions" style={{ justifyContent: "space-between" }}>
                        <div>
                          <h3>{item.name}</h3>
                          <p className="muted">
                            {item.valve_code} · {labelOf(METHOD_LABEL, item.method)} <StatusBadge>{item.status}</StatusBadge>
                          </p>
                        </div>
                        <DataSourceBadge source={item.data_source} />
                      </div>
                      <div className="grid three compact">
                        <div>
                          <div className="label">墒情 / 阈值</div>
                          <strong>
                            {item.moisture_pct == null ? "—" : `${item.moisture_pct}%`}
                            {agronomy?.threshold_pct != null ? ` / ${agronomy.threshold_pct}%` : ""}
                          </strong>
                          <div className="muted">{labelOf(MOISTURE_STATUS_LABEL, agronomy?.moisture_status)}</div>
                        </div>
                        <div>
                          <div className="label">ET 核算</div>
                          <strong>
                            ET₀ {agronomy?.et0_mm ?? "—"} · Kc {agronomy?.kc ?? "—"} · ETc {agronomy?.etc_mm ?? "—"} mm
                          </strong>
                          <div className="muted">{agronomy?.window_hint}</div>
                        </div>
                        <div>
                          <div className="label">建议水量</div>
                          <strong>
                            {item.recommendation_mm ?? 0} mm
                            {agronomy?.volume_m3 ? ` · ${agronomy.volume_m3} m³` : ""}
                          </strong>
                          <div className="muted">
                            定额 {item.used_m3}/{item.budget_m3} m³
                          </div>
                        </div>
                      </div>
                      <p>{item.recommendation}</p>
                      {agronomy?.reasons?.length ? (
                        <ul className="why-list">
                          {agronomy.reasons.slice(0, 4).map((line) => (
                            <li key={line}>{line}</li>
                          ))}
                        </ul>
                      ) : null}
                      <div className="row-actions">
                        {item.accept_allowed ? (
                          <button className="btn" disabled={busy === item.id} onClick={() => void accept(item.id)}>
                            {busy === item.id ? "正在登记…" : "采纳为任务"}
                          </button>
                        ) : (
                          <span className="muted">{item.status === "accepted" ? "已转为任务，仍未下发阀控。" : "今日无需生成新任务。"}</span>
                        )}
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        </>
      )}
    </DataPageState>
  );
}
