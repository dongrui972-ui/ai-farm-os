import { api } from "../api";
import { DataSourceBadge, ErrorText, Loading, PageHeader, RiskBadge, StatusBadge } from "../components/Ui";
import { useLoad } from "../hooks";

export function PlantsPage() {
  const { data, error } = useLoad(() => api.plants());
  if (error) return <ErrorText error={error} />;
  if (!data) return <Loading />;
  return (
    <>
      <PageHeader title="作物" subtitle="本季在田作物与生育期。健康状态由农技员登记；分区墒情仅为仿真对照。" />
      <section className="card">
        <table>
          <thead>
            <tr>
              <th>分区</th>
              <th>作物 / 品种</th>
              <th>生育期</th>
              <th>健康</th>
              <th>墒情对照</th>
              <th>来源</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item) => (
              <tr key={item.id}>
                <td>{item.zone_code}</td>
                <td>
                  {item.crop_name} · {item.variety}
                  <div className="muted">
                    {item.planted_at} → {item.expected_harvest}
                  </div>
                </td>
                <td>{item.growth_stage}</td>
                <td>
                  <StatusBadge>{item.health_status}</StatusBadge>
                  <div className="muted">{item.notes}</div>
                </td>
                <td>
                  {item.moisture_pct == null ? "—" : `${item.moisture_pct}%`}
                  {item.risk_level ? (
                    <div>
                      <RiskBadge level={item.risk_level} />
                    </div>
                  ) : null}
                </td>
                <td>
                  <DataSourceBadge source={item.data_source} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
