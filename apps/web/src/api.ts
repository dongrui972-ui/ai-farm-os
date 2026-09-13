import type {
  AIJobCreateInput,
  AgentItem,
  AgentRun,
  AIJobItem,
  Architecture,
  AssetItem,
  Dashboard,
  DeviceItem,
  DiagnosisCreateInput,
  DiagnosisItem,
  FleetItem,
  IrrigationItem,
  LotItem,
  Meta,
  NoteCreateInput,
  NoteItem,
  PlantItem,
  RobotCommandInput,
  RobotItem,
  Season,
  TaskCreateInput,
  TaskItem,
  TaskPatchInput,
  TwinPayload,
  VendorItem,
  Workbench,
} from "./types";
import { ApiClient } from "./api/client";

const client = new ApiClient("/api");

export const api = {
  meta: () => client.request<Meta>("/meta"),
  dashboard: () => client.request<Dashboard>("/dashboard"),
  twin: (layers?: string[]) =>
    client.request<TwinPayload>(
      client.pathWithQuery("/twin", {
        layers: layers?.length ? layers.join(",") : undefined,
      }),
    ),
  assets: () => client.request<AssetItem[]>("/assets"),
  plants: () => client.request<PlantItem[]>("/plants"),
  irrigation: () => client.request<IrrigationItem[]>("/irrigation"),
  acceptIrrigation: (id: string) =>
    client.request<{ task: TaskItem; note: string }>(`/irrigation/${id}/accept-recommendation`, {
      method: "POST",
      body: {},
    }),
  tasks: () => client.request<TaskItem[]>("/tasks"),
  createTask: (body: TaskCreateInput) => client.request<TaskItem>("/tasks", { method: "POST", body }),
  patchTask: (id: string, body: TaskPatchInput) => client.request<TaskItem>(`/tasks/${id}`, { method: "PATCH", body }),
  devices: () => client.request<DeviceItem[]>("/devices"),
  device: (id: string) => client.request<DeviceItem>(`/devices/${id}`),
  agents: () => client.request<AgentItem[]>("/agents"),
  agent: (id: string) => client.request<AgentItem>(`/agents/${id}`),
  runAgent: (id: string) => client.request<AgentRun>(`/agents/${id}/run`, { method: "POST", body: {} }),
  diagnoses: () => client.request<DiagnosisItem[]>("/diagnoses"),
  createDiagnosis: (body: DiagnosisCreateInput) => client.request<DiagnosisItem>("/diagnoses", { method: "POST", body }),
  jobs: () => client.request<AIJobItem[]>("/ai-center/jobs"),
  createJob: (body: AIJobCreateInput) =>
    client.request<AIJobItem>("/ai-center/jobs", {
      method: "POST",
      body,
    }),
  robots: () => client.request<RobotItem[]>("/robots"),
  robotCommand: (id: string, body: RobotCommandInput) =>
    client.request<unknown>(`/robots/${id}/command`, {
      method: "POST",
      body,
    }),
  fleet: () => client.request<FleetItem[]>("/fleet"),
  postharvest: () => client.request<LotItem[]>("/postharvest"),
  vendors: () => client.request<VendorItem[]>("/vendors"),
  collaboration: () => client.request<NoteItem[]>("/collaboration"),
  createNote: (body: NoteCreateInput) => client.request<NoteItem>("/collaboration", { method: "POST", body }),
  architecture: () => client.request<Architecture>("/architecture"),
  workbench: () => client.request<Workbench>("/workbench"),
  seasons: () => client.request<Season[]>("/seasons"),
};
