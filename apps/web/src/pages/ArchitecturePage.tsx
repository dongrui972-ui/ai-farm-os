import { api } from "../api";
import { ErrorText, Loading, PageHeader } from "../components/Ui";
import { useLoad } from "../hooks";

export function ArchitecturePage() {
  const { data, error } = useLoad(() => api.architecture());
  if (error) return <ErrorText error={error} />;
  if (!data) return <Loading />;
  return (
    <>
      <PageHeader title="系统架构" subtitle="Unified Mainline 的真实边界。PowerShell Demo 只作产品交互参考，未复制其技术栈。" />
      <div className="grid two">
        <section className="card">
          <h2>{data.product}</h2>
          <p>{data.farm}</p>
          <ul>
            <li>Web：{data.stack.web}</li>
            <li>API：{data.stack.api}</li>
            <li>数据：{data.stack.db}</li>
          </ul>
          {Object.entries(data.modules).map(([key, mods]) => (
            <p key={key}>
              <strong>{key}</strong> · {mods.join(" / ")}
            </p>
          ))}
        </section>
        <section className="card">
          <h2>能力边界</h2>
          <ul>
            {data.boundaries.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      </div>
    </>
  );
}
