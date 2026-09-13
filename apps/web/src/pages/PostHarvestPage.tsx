import { api } from "../api";
import { DataPageState } from "../components/PageState";
import { DataSourceBadge, PageHeader } from "../components/Ui";
import { useLoad } from "../hooks";

export function PostHarvestPage() {
  const { data, error } = useLoad(() => api.postharvest());
  return (
    <DataPageState data={data} error={error}>
      {(rows) => (
        <>
          <PageHeader title="采后" subtitle="预冷与分拣批次台账。库温不冒充在线冷链。" />
          <div className="grid cards">
            {rows.map((lot) => (
              <article className="card" key={lot.id}>
                <h3>
                  {lot.crop_name} {lot.quantity_kg} kg
                </h3>
                <p>
                  {lot.grade} 级 · {lot.location}
                </p>
                <p className="muted">
                  {lot.harvested_at} → {lot.destination}
                </p>
                <p>{lot.notes}</p>
                <DataSourceBadge source={lot.data_source} />
              </article>
            ))}
          </div>
        </>
      )}
    </DataPageState>
  );
}
