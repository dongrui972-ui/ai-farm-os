import { api } from "../api";
import { DataPageState } from "../components/PageState";
import { DataSourceBadge, EmptyState, PageHeader, StatusBadge } from "../components/Ui";
import { useLoad } from "../hooks";

export function AssetsPage() {
  const { data, error, reload } = useLoad(() => api.assets());
  return (
    <DataPageState data={data} error={error} onRetry={reload}>
      {(rows) => (
        <>
          <PageHeader title="资产台账" subtitle="温室、泵、阀、冷库与包装线。状态来自人工登记，不是在线健康度。" />
          <section className="card">
            {rows.length === 0 ? (
              <EmptyState title="没有资产记录" hint="示范场种子应包含温室骨架与泵阀。" />
            ) : (
              <div className="table-wrap">
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
              </div>
            )}
          </section>
        </>
      )}
    </DataPageState>
  );
}
