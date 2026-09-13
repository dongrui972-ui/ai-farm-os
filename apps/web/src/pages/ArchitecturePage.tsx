import { api } from "../api";
import { DataPageState } from "../components/PageState";
import { PageHeader } from "../components/Ui";
import { useLoad } from "../hooks";

export function ArchitecturePage() {
  const { data, error } = useLoad(() => api.architecture());
  return (
    <DataPageState data={data} error={error}>
      {(detail) => (
        <>
          <PageHeader title="系统架构" subtitle="Unified Mainline 的真实边界。PowerShell Demo 只作产品交互参考，未复制其技术栈。" />
          <div className="grid two">
            <section className="card">
              <h2>{detail.product}</h2>
              <p>{detail.farm}</p>
              <ul>
                <li>Web：{detail.stack.web}</li>
                <li>API：{detail.stack.api}</li>
                <li>数据：{detail.stack.db}</li>
              </ul>
              {Object.entries(detail.modules).map(([key, mods]) => (
                <p key={key}>
                  <strong>{key}</strong> · {mods.join(" / ")}
                </p>
              ))}
            </section>
            <section className="card">
              <h2>能力边界</h2>
              <ul>
                {detail.boundaries.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </section>
          </div>
        </>
      )}
    </DataPageState>
  );
}
