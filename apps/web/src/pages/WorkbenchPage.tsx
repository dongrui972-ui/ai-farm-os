import { api } from "../api";
import { ErrorText, Loading, PageHeader } from "../components/Ui";
import { useLoad } from "../hooks";

export function WorkbenchPage() {
  const { data, error } = useLoad(() => api.workbench());
  if (error) return <ErrorText error={error} />;
  if (!data) return <Loading />;
  return (
    <>
      <PageHeader title={data.title} subtitle={`${data.focus_date} 的水肥拍板、执行队列与协同留言。`} />
      <div className="grid three">
        {data.blocks.map((block) => (
          <section className="card" key={block.id}>
            <h2>{block.title}</h2>
            {block.items.map((item, index) => (
              <article key={String(item.id ?? index)} className="card" style={{ marginBottom: 8 }}>
                <strong>{String(item.title ?? item.name ?? item.author ?? "条目")}</strong>
                <p className="muted">{String(item.recommendation ?? item.notes ?? item.body ?? "")}</p>
              </article>
            ))}
          </section>
        ))}
      </div>
    </>
  );
}
