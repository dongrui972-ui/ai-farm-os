import { useState } from "react";
import { api } from "../api";
import { DataSourceBadge, ErrorText, Loading, PageHeader } from "../components/Ui";
import { useLoad } from "../hooks";

export function CollaborationPage() {
  const { data, error, reload } = useLoad(() => api.collaboration());
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  if (error) return <ErrorText error={error} />;
  if (!data) return <Loading />;
  return (
    <>
      <PageHeader title="协作" subtitle="场长、农技员与采收组的留言。不是即时通讯，也不是设备指令通道。" />
      <section className="card form" style={{ marginBottom: 14 }}>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="标题" />
        <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={3} placeholder="内容" />
        <button
          className="btn"
          disabled={!title || !body}
          onClick={() =>
            void api
              .createNote({ author: "值班", role: "现场", title, body, related_module: "workbench" })
              .then(() => {
                setTitle("");
                setBody("");
                reload();
              })
          }
        >
          发布
        </button>
      </section>
      <div className="grid cards">
        {data.map((note) => (
          <article className="card" key={note.id}>
            <h3>{note.title}</h3>
            <p className="muted">
              {note.author} · {note.role} · {note.created_at}
            </p>
            <p>{note.body}</p>
            <DataSourceBadge source={note.data_source} />
          </article>
        ))}
      </div>
    </>
  );
}
