import { api } from "../api";
import { DataPageState } from "../components/PageState";
import { EmptyState, PageHeader } from "../components/Ui";
import { useLoad } from "../hooks";

export function WorkbenchPage() {
  const { data, error, reload } = useLoad(() => api.workbench());
  return (
    <DataPageState data={data} error={error} onRetry={reload}>
      {(workbench) => (
        <>
          <PageHeader title={workbench.title} subtitle={`${workbench.focus_date} 的水肥拍板、执行队列与协同留言。`} />
          <div className="grid three">
            {workbench.blocks.map((block) => (
              <section className="card" key={block.id}>
                <h2>{block.title}</h2>
                {block.items.length === 0 ? (
                  <EmptyState title="本栏暂无条目" hint="没有待办时保持空白，不编造忙碌感。" />
                ) : (
                  block.items.map((item, index) => (
                    <article key={String(item.id ?? index)} className="card" style={{ marginBottom: 8 }}>
                      <strong>{String(item.title ?? item.name ?? item.author ?? "条目")}</strong>
                      <p className="muted">{String(item.recommendation ?? item.notes ?? item.body ?? "")}</p>
                    </article>
                  ))
                )}
              </section>
            ))}
          </div>
        </>
      )}
    </DataPageState>
  );
}
