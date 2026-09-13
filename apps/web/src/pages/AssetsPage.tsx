import { api } from "../api";
import { DataPageState } from "../components/PageState";
import { DataSourceBadge, PageHeader, StatusBadge } from "../components/Ui";
import { useLoad } from "../hooks";

export function AssetsPage() {
  const { data, error } = useLoad(() => api.assets());
  return (
    <DataPageState data={data} error={error}>
      {(rows) => (
        <>
          <PageHeader title="资产台账" subtitle="温室、泵、阀、冷库与包装线。状态来自人工登记，不是在线健康度。" />
          <section className="card">
            <table>
              <thead>
                <tr>
                  <th>资产</th>
                  <th>类型</th>
                  <th>分区</th>
                  <th>投用</th>
                  <th>备注</th>
                  <th>来源</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((item) => (
                  <tr key={item.id}>
                    <td>
                      {item.name}
                      <div className="muted">
                        <StatusBadge>{item.status}</StatusBadge>
                      </div>
                    </td>
                    <td>{item.asset_type}</td>
                    <td>{item.zone_code}</td>
                    <td>{item.commissioned_at}</td>
                    <td>{item.notes}</td>
                    <td>
                      <DataSourceBadge source={item.data_source} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      )}
    </DataPageState>
  );
}
