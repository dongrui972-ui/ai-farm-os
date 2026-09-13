import type { TwinDevice, TwinZone } from "../types";

const CROP_COLOR: Record<string, string> = {
  番茄: "#c45c4a",
  黄瓜: "#4f8f4c",
  彩椒: "#d89b2c",
  草莓: "#c43b5a",
  生菜: "#6aa85a",
  菠菜: "#3e7a46",
  玉米: "#c9b04a",
};

function moistureColor(value: number | null) {
  if (value == null) return "#c9c2b3";
  if (value < 45) return "#c47b3b";
  if (value < 55) return "#d7b35a";
  return "#4d8f6a";
}

function riskColor(level: string) {
  if (level === "high") return "#c25a4e";
  if (level === "medium") return "#d4a24a";
  return "#7aa17c";
}

function zoneFill(zone: TwinZone, layer: string) {
  if (zone.zone_type === "water") return "#6fa4c8";
  if (zone.zone_type === "facility") return "#b7b1a4";
  if (layer === "moisture") return moistureColor(zone.moisture_pct);
  if (layer === "risk") return riskColor(zone.risk_level);
  if (layer === "crop") return zone.crop_name ? CROP_COLOR[zone.crop_name] ?? "#8aa36d" : "#c9c2b3";
  return "#8aa36d";
}

function toPoints(zone: TwinZone) {
  return zone.polygon.map((p) => `${p.x},${p.y}`).join(" ");
}

export function FarmMap({
  zones,
  devices,
  layer,
  selectedId,
  onSelect,
}: {
  zones: TwinZone[];
  devices?: TwinDevice[];
  layer: string;
  selectedId?: string | null;
  onSelect?: (id: string) => void;
}) {
  const showDevices = layer === "device" || layer === "sensors";
  return (
    <svg className="map-svg" viewBox="0 0 940 660" role="img" aria-label="示范农场示意地图">
      <rect x="0" y="0" width="940" height="660" fill="#d7e2cc" />
      <path d="M430 40 L430 620" stroke="#c4b79f" strokeWidth="18" />
      <path d="M20 360 L900 360" stroke="#c4b79f" strokeWidth="10" />
      <text x="40" y="50" fill="#4c5a46" fontSize="16">
        温室区
      </text>
      <text x="500" y="50" fill="#4c5a46" fontSize="16">
        露地区 / 设施
      </text>
      {zones.map((zone) => (
        <g key={zone.id} onClick={() => onSelect?.(zone.id)} style={{ cursor: "pointer" }}>
          <polygon
            points={toPoints(zone)}
            fill={zoneFill(zone, layer)}
            stroke={selectedId === zone.id ? "#1c241c" : "#efe8dc"}
            strokeWidth={selectedId === zone.id ? 4 : 2}
            opacity={0.92}
          />
          <text
            x={zone.polygon[0].x + 12}
            y={zone.polygon[0].y + 22}
            fill="#1c241c"
            fontSize="13"
            fontWeight="700"
          >
            {zone.code}
          </text>
          <text x={zone.polygon[0].x + 12} y={zone.polygon[0].y + 40} fill="#243028" fontSize="11">
            {layer === "moisture" && zone.moisture_pct != null
              ? `${zone.moisture_pct}%`
              : layer === "crop"
                ? zone.crop_name ?? zone.zone_type
                : layer === "risk"
                  ? zone.risk_level
                  : zone.name.replace(/^[A-Z0-9]+ /, "")}
          </text>
        </g>
      ))}
      {showDevices &&
        devices?.map((device) =>
          device.map_x != null && device.map_y != null ? (
            <g key={device.id}>
              <circle
                cx={device.map_x}
                cy={device.map_y}
                r={layer === "sensors" ? 8 : 6}
                fill={device.status === "unbound" ? "#8a7b68" : "#1d4e3a"}
                stroke="#fffaf2"
                strokeWidth="2"
              />
              {layer === "sensors" && (
                <text x={device.map_x + 10} y={device.map_y + 4} fontSize="11" fill="#1c241c">
                  {device.last_value ? `${device.last_value}${device.unit ?? ""}` : device.name}
                </text>
              )}
            </g>
          ) : null,
        )}
    </svg>
  );
}
