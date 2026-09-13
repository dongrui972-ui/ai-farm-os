import { api } from "../api";
import { DataPageState } from "../components/PageState";
import { DataSourceBadge, PageHeader, StatusBadge } from "../components/Ui";
import { useLoad } from "../hooks";

export function SeasonsPage() {
  const { data, error } = useLoad(() => api.seasons());
  return (
    <DataPageState data={data} error={error}>
      {(rows) => (
        <>
          <PageHeader title="本季与历史" subtitle="茬口台账。当前演示锚定 2026 秋茬。" />
          <div className="grid cards">
            {rows.map((season) => (
              <article className="card" key={season.id}>
                <h3>{season.name}</h3>
                <StatusBadge>{season.status}</StatusBadge>
                <p>
                  {season.start_date} — {season.end_date}
                </p>
                <p className="muted">{season.notes}</p>
                <DataSourceBadge source={season.data_source} />
              </article>
            ))}
          </div>
        </>
      )}
    </DataPageState>
  );
}
