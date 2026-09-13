import { useState } from "react";
import { api } from "../api";
import { DataPageState } from "../components/PageState";
import { DataSourceBadge, PageHeader, StatusBadge } from "../components/Ui";
import { useLoad } from "../hooks";
import type { DeviceItem } from "../types";

export function DevicesPage() {
  const { data, error } = useLoad(() => api.devices());
  const [detail, setDetail] = useState<DeviceItem | null>(null);
  return (
    <DataPageState data={data} error={error}>
      {(rows) => (
        <>
          <PageHeader
            title="设备"
            subtitle="传感与阀门遥测。仿真在线 ≠ 现场在线。未接入设备不展示伪造心跳。"
          />
          <div className="grid two">
            <section className="card">
              <table>
                <thead>
                  <tr>
                    <th>设备</th>
                    <th>读数</th>
                    <th>状态</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <button className="btn ghost" onClick={() => void api.device(item.id).then(setDetail)}>
                          {item.name}
                        </button>
                        <div className="muted">
                          {item.zone_code} · {item.device_type}
                        </div>
                      </td>
                      <td>{item.last_value ? `${item.last_value} ${item.unit}` : "无"}</td>
                      <td>
                        <StatusBadge>{item.status_label ?? item.status}</StatusBadge>
                        <div>
                          <DataSourceBadge source={item.data_source} />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
            <section className="card">
              {detail ? (
                <>
                  <h2>{detail.name}</h2>
                  <p>{detail.binding_note}</p>
                  <p>
                    live = {String(detail.live)} <DataSourceBadge source={detail.data_source} />
                  </p>
                  <table>
                    <thead>
                      <tr>
                        <th>时间</th>
                        <th>值</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.readings?.map((row) => (
                        <tr key={row.id}>
                          <td>{row.recorded_at}</td>
                          <td>
                            {row.value}
                            {row.unit}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              ) : (
                <p className="muted">选择设备查看仿真/抄表序列。</p>
              )}
            </section>
          </div>
        </>
      )}
    </DataPageState>
  );
}
