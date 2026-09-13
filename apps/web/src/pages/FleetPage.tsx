import { api } from "../api";
import { DataPageState } from "../components/PageState";
import { DataSourceBadge, PageHeader, StatusBadge } from "../components/Ui";
import { useLoad } from "../hooks";

export function FleetPage() {
  const { data, error } = useLoad(() => api.fleet());
  return (
    <DataPageState data={data} error={error}>
      {(rows) => (
        <>
          <PageHeader title="车队" subtitle="位置来自出车单或人工登记，不是车辆 GPS。" />
          <section className="card">
            <table>
              <thead>
                <tr>
                  <th>车辆</th>
                  <th>状态</th>
                  <th>登记位置</th>
                  <th>保养</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((item) => (
                  <tr key={item.id}>
                    <td>
                      {item.name}
                      <div className="muted">
                        {item.vehicle_type} · {item.operator}
                      </div>
                    </td>
                    <td>
                      <StatusBadge>{item.status}</StatusBadge>
                    </td>
                    <td>
                      {item.last_known_place}
                      <div className="muted">{item.notes}</div>
                    </td>
                    <td>
                      {item.last_service}
                      <div>
                        <DataSourceBadge source={item.data_source} />
                      </div>
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
