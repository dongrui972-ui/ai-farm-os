import { useState } from "react";
import { api } from "../api";
import { DataPageState } from "../components/PageState";
import { FarmMap } from "../components/FarmMap";
import { DataSourceBadge, EmptyState, PageHeader, RiskBadge } from "../components/Ui";
import { useLoad } from "../hooks";
import { MOISTURE_STATUS_LABEL, labelOf } from "../labels";
import type { TwinLayerKey } from "../types";

const LAYERS = [
  { id: "moisture", label: "墒情" },
  { id: "crop", label: "作物" },
  { id: "risk", label: "风险" },
  { id: "device", label: "设备" },
  { id: "sensors", label: "传感器" },
] as const satisfies { id: TwinLayerKey; label: string }[];

const LAYER_HELP: Record<TwinLayerKey, string> = {
  moisture: "颜色按仿真含水率相对该作物灌水阈值着色，不是直播探针。低于阈值偏干。",
  crop: "颜色按作物种类。生育期与品种来自 MANUAL 台账。",
  risk: "综合水分胁迫、棚湿与植保假设，不是自动处方。",
  device: "深色点为仿真或抄表位，灰色点为未接入硬件。",
  sensors: "标注最近一条仿真/抄表读数，无实时推流。",
};

export function TwinPage() {
  const [layer, setLayer] = useState<TwinLayerKey>("moisture");
  const [selectedId, setSelectedId] = useState<string | null>("zone-a3");
  const { data, error, reload } = useLoad(() => api.twin(["moisture", "crop", "risk", "device", "sensors"]), []);

  return (
    <DataPageState data={data} error={error} onRetry={reload}>
      {(payload) => {
        const selected = payload.zones.find((zone) => zone.id === selectedId);
        const agronomy = selected?.agronomy;
        return (
          <>
            <PageHeader
              title="数字孪生 · 五层"
              subtitle="墒情 / 作物 / 风险 / 设备 / 传感器。地图是场内示意网格。点选分区可看到阈值、Kc 与建议，全部标仿真或台账。"
            />
            {payload.weather ? (
              <section className="weather-strip">
                <div>
                  <strong>仿真气象</strong>
                  <span>
                    ET₀ {payload.weather.et0_mm} mm · {payload.weather.sky} · 棚室 ET 已按 0.78 折减
                  </span>
                </div>
                <DataSourceBadge source={payload.weather.data_source} />
              </section>
            ) : null}
            <div className="layer-bar">
              {LAYERS.map((item) => (
                <button key={item.id} className={layer === item.id ? "on" : ""} onClick={() => setLayer(item.id)}>
                  {item.label}
                </button>
              ))}
            </div>
            <div className="map-wrap">
              <section className="card map-card">
                <FarmMap
                  zones={payload.zones}
                  devices={payload.devices}
                  layer={layer}
                  selectedId={selectedId}
                  onSelect={setSelectedId}
                />
                <p className="muted">{payload.disclaimer}</p>
              </section>
              <aside className="card">
                {selected ? (
                  <>
                    <h2>
                      {selected.code} {selected.crop_name ?? selected.zone_type}
                    </h2>
                    <p className="muted">{selected.name}</p>
                    <p>
                      <RiskBadge level={selected.risk_level} /> <DataSourceBadge source={selected.data_source} />
                    </p>
                    <p>
                      墒情：{selected.moisture_pct == null ? "无（设施/水面）" : `${selected.moisture_pct}%`}
                      {agronomy?.threshold_pct != null ? ` · 阈值 ${agronomy.threshold_pct}%` : ""} ·{" "}
                      {labelOf(MOISTURE_STATUS_LABEL, agronomy?.moisture_status)}
                    </p>
                    <p>
                      作物：{selected.variety ?? "—"} · {selected.growth_stage ?? "—"}
                      {agronomy?.kc != null ? ` · Kc ${agronomy.kc}` : ""}
                    </p>
                    <p>{selected.risk_note}</p>
                    {agronomy?.applicable ? (
                      <>
                        <hr />
                        <h3>{agronomy.action_label}</h3>
                        <p>{agronomy.summary}</p>
                        <p className="muted">
                          ETc {agronomy.etc_mm} mm/d · 建议 {agronomy.recommended_mm} mm · {agronomy.window_hint}
                        </p>
                        <ul className="why-list">
                          {(agronomy.reasons ?? []).slice(0, 3).map((line) => (
                            <li key={line}>{line}</li>
                          ))}
                        </ul>
                      </>
                    ) : (
                      <p className="muted">该分区不参与水量平衡计算。</p>
                    )}
                  </>
                ) : (
                  <EmptyState title="未选择分区" hint="点选地图上的温室或露地查看详情。" />
                )}
                <hr />
                <h3>本层含义</h3>
                <p className="muted">{LAYER_HELP[layer]}</p>
              </aside>
            </div>
          </>
        );
      }}
    </DataPageState>
  );
}
