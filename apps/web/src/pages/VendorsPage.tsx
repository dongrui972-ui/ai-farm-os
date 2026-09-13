import { api } from "../api";
import { DataPageState } from "../components/PageState";
import { DataSourceBadge, PageHeader } from "../components/Ui";
import { useLoad } from "../hooks";

export function VendorsPage() {
  const { data, error } = useLoad(() => api.vendors());
  return (
    <DataPageState data={data} error={error}>
      {(rows) => (
        <>
          <PageHeader title="供应商" subtitle="种子、肥料、农膜与包装的往来台账。" />
          <section className="card">
            <table>
              <thead>
                <tr>
                  <th>供应商</th>
                  <th>品类</th>
                  <th>联系人</th>
                  <th>备注</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((item) => (
                  <tr key={item.id}>
                    <td>
                      {item.name}
                      <div>
                        <DataSourceBadge source={item.data_source} />
                      </div>
                    </td>
                    <td>{item.category}</td>
                    <td>
                      {item.contact} {item.phone}
                    </td>
                    <td>
                      {item.rating} · {item.notes}
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
