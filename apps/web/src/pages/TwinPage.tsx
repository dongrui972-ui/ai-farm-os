import { useState } from "react";
import { api } from "../api";
import { FarmMap } from "../components/FarmMap";
import { DataSourceBadge, ErrorText, Loading, PageHeader, RiskBadge } from "../components/Ui";
import { useLoad } from "../hooks";

const LAYERS = [
  { id: "moisture", label: "墒情" },
  { id: "crop", label: "作物" },
  { id: "risk", label: "风险" },
  { id: "device", label: "设备" },
  { id: "sensors", label: "传感器" },
];

export function TwinPage() {
  const [layer, setLayer] = useState("moisture");
  const [selectedId, setSelectedId] = useState<string | null>("zone-a3");
  const { data, error } = useLoad(() => api.twin(["moisture", "crop", "risk", "device", "sensors"]), []);
  const selected = data?.zones.find((z) => z.id === selectedId);

  if (error) return <ErrorText error={error} />;
  if (!data) return <Loading />;

  return (
    <>
      <PageHeader
        title="数字孪生 · 五层"
        subtitle="墒情 / 作物 / 风险 / 设备 / 传感器。地图是场内示意网格。点位数值来自仿真回放或人工抄表，不是直播机身。"
      />
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
            zones={data.zones}
            devices={data.devices}
            layer={layer}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
          <p className="muted">{data.disclaimer}</p>
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
              <p>墒情：{selected.moisture_pct == null ? "无（设施/水面）" : `${selected.moisture_pct}% · 仿真`}</p>
              <p>作物：{selected.variety ?? "—"} · {selected.growth_stage ?? "—"}</p>
              <p>{selected.risk_note}</p>
            </>
          ) : (
            <p className="muted">点选分区查看详情。</p>
          )}
          <hr />
          <h3>本层含义</h3>
          <p className="muted">
            {layer === "moisture" && "颜色表示仿真 0–20cm 体积含水率。低于 45% 偏干。"}
            {layer === "crop" && "颜色按作物种类，台账来源 MANUAL。"}
            {layer === "risk" && "综合水分胁迫与植保假设，不是自动处方。"}
            {layer === "device" && "深色点为仿真或抄表位，灰色点为未接入硬件。"}
            {layer === "sensors" && "标注最近一条仿真/抄表读数，无实时推流。"}
          </p>
        </aside>
      </div>
    </>
  );
}
