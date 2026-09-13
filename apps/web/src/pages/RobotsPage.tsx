import { useState } from "react";
import { api } from "../api";
import { DataSourceBadge, ErrorText, Loading, PageHeader } from "../components/Ui";
import { useLoad } from "../hooks";

export function RobotsPage() {
  const { data, error } = useLoad(() => api.robots());
  const [reject, setReject] = useState("");
  if (error) return <ErrorText error={error} />;
  if (!data) return <Loading />;
  return (
    <>
      <PageHeader
        title="机器人（能力边界）"
        subtitle="本模块为 stub。不绘制伪造 GPS 轨迹，不接受运动或喷雾指令。"
      />
      <div className="callout danger">
        last_pose 恒为空。任何 /robots/{"{id}"}/command 返回 409 robot_unbound。
      </div>
      {reject ? <pre className="card">{reject}</pre> : null}
      <div className="grid cards" style={{ marginTop: 14 }}>
        {data.map((robot) => (
          <article className="card" key={robot.id}>
            <h3>{robot.name}</h3>
            <p className="muted">
              {robot.robot_type} · {robot.status}
            </p>
            <p>{robot.capability_boundary}</p>
            <p>位姿：{robot.last_pose ?? "无（未接入）"}</p>
            <DataSourceBadge source={robot.data_source} />
            <div style={{ marginTop: 10 }}>
              <button
                className="btn danger"
                onClick={() =>
                  api
                    .robotCommand(robot.id, "goto")
                    .catch((err: unknown) => {
                      const raw = err instanceof Error ? err.message : "已拒绝";
                      try {
                        const parsed = JSON.parse(raw) as { detail?: { message?: string } };
                        setReject(parsed.detail?.message ?? raw);
                      } catch {
                        setReject(raw);
                      }
                    })
                }
              >
                尝试下发行走（应被拒绝）
              </button>
            </div>
          </article>
        ))}
      </div>
    </>
  );
}
