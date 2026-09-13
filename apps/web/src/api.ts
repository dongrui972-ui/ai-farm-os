import type {
  AgentItem,
  AgentRun,
  AIJobItem,
  Architecture,
  AssetItem,
  Dashboard,
  DeviceItem,
  DiagnosisItem,
  FleetItem,
  IrrigationItem,
  LotItem,
  Meta,
  NoteItem,
  PlantItem,
  RobotItem,
  Season,
  TaskItem,
  TwinPayload,
  VendorItem,
  Workbench,
} from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return (await res.json()) as T;
}

export const api = {
  meta: () => request<Meta>("/api/meta"),
  dashboard: () => request<Dashboard>("/api/dashboard"),
  twin: (layers?: string[]) =>
    request<TwinPayload>(`/api/twin${layers?.length ? `?layers=${layers.join(",")}` : ""}`),
  assets: () => request<AssetItem[]>("/api/assets"),
  plants: () => request<PlantItem[]>("/api/plants"),
  irrigation: () => request<IrrigationItem[]>("/api/irrigation"),
  acceptIrrigation: (id: string) =>
    request<{ task: TaskItem; note: string }>(`/api/irrigation/${id}/accept-recommendation`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
  tasks: () => request<TaskItem[]>("/api/tasks"),
  createTask: (body: Partial<TaskItem> & { title: string }) =>
    request<TaskItem>("/api/tasks", { method: "POST", body: JSON.stringify(body) }),
  patchTask: (id: string, body: Partial<TaskItem>) =>
    request<TaskItem>(`/api/tasks/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  devices: () => request<DeviceItem[]>("/api/devices"),
  device: (id: string) => request<DeviceItem>(`/api/devices/${id}`),
  agents: () => request<AgentItem[]>("/api/agents"),
  agent: (id: string) => request<AgentItem>(`/api/agents/${id}`),
  runAgent: (id: string) => request<AgentRun>(`/api/agents/${id}/run`, { method: "POST", body: "{}" }),
  diagnoses: () => request<DiagnosisItem[]>("/api/diagnoses"),
  createDiagnosis: (body: Partial<DiagnosisItem> & { title: string; symptom: string }) =>
    request<DiagnosisItem>("/api/diagnoses", { method: "POST", body: JSON.stringify(body) }),
  jobs: () => request<AIJobItem[]>("/api/ai-center/jobs"),
  createJob: (title: string) =>
    request<AIJobItem>("/api/ai-center/jobs", {
      method: "POST",
      body: JSON.stringify({ title, job_type: "briefing" }),
    }),
  robots: () => request<RobotItem[]>("/api/robots"),
  robotCommand: (id: string, command: string) =>
    request<unknown>(`/api/robots/${id}/command`, {
      method: "POST",
      body: JSON.stringify({ command }),
    }),
  fleet: () => request<FleetItem[]>("/api/fleet"),
  postharvest: () => request<LotItem[]>("/api/postharvest"),
  vendors: () => request<VendorItem[]>("/api/vendors"),
  collaboration: () => request<NoteItem[]>("/api/collaboration"),
  createNote: (body: Pick<NoteItem, "author" | "role" | "title" | "body" | "related_module">) =>
    request<NoteItem>("/api/collaboration", { method: "POST", body: JSON.stringify(body) }),
  architecture: () => request<Architecture>("/api/architecture"),
  workbench: () => request<Workbench>("/api/workbench"),
  seasons: () => request<Season[]>("/api/seasons"),
};
