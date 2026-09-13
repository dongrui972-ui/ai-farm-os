export type DataSource = "REAL" | "SIMULATION" | "MANUAL";
export type TwinLayerKey = "moisture" | "crop" | "risk" | "device" | "sensors";
export type RiskLevel = "low" | "medium" | "high";
export type TaskStatus = "todo" | "in_progress" | "done" | "cancelled";
export type TaskPriority = "low" | "normal" | "high" | "urgent";
export type DecisionUrgency = "urgent" | "high" | "normal";
export type ZoneType = "greenhouse" | "open_field" | "water" | "facility";

export type Farm = {
  id: string;
  name: string;
  location: string;
  operator: string;
  area_mu: number;
  description: string;
  current_season_id: string | null;
};

export type Season = {
  id: string;
  name: string;
  year: number;
  start_date: string;
  end_date: string;
  status: string;
  notes: string;
  data_source: DataSource;
};

export type Meta = {
  name: string;
  line: string;
  farm: Farm | null;
  season: Season | null;
  data_policy: { allowed_sources: DataSource[]; rule: string };
  layers: TwinLayerKey[];
};

export type Decision = {
  id: string;
  kind: string;
  urgency: DecisionUrgency;
  title: string;
  detail: string;
  zone_id: string | null;
  href: string;
  action_label: string;
  data_source: DataSource;
};

export type Dashboard = {
  farm: Farm | null;
  season: Season | null;
  generated_at: string;
  decisions: Decision[];
  kpis: { key: string; label: string; value: number }[];
  risk_zones: {
    id: string;
    code: string;
    name: string;
    risk_level: RiskLevel;
    risk_note: string;
    moisture_pct: number | null;
    data_source: DataSource;
  }[];
  open_tasks: TaskItem[];
  data_source_legend: { source: DataSource; label: string; note: string }[];
};

export type TwinZone = {
  id: string;
  code: string;
  name: string;
  zone_type: ZoneType;
  polygon: { x: number; y: number }[];
  moisture_pct: number | null;
  risk_level: RiskLevel;
  risk_note: string;
  crop_name: string | null;
  variety: string | null;
  growth_stage: string | null;
  data_source: DataSource;
};

export type TwinDevice = {
  id: string;
  name: string;
  device_type: string;
  status: string;
  metric: string | null;
  last_value: string | null;
  unit: string | null;
  map_x: number | null;
  map_y: number | null;
  data_source: DataSource;
  binding_note: string;
};

export type TwinPayload = {
  layers: TwinLayerKey[];
  available_layers: { id: TwinLayerKey; label: string; data_source: DataSource }[];
  zones: TwinZone[];
  devices?: TwinDevice[];
  disclaimer: string;
};

export type AssetItem = {
  id: string;
  zone_id: string | null;
  name: string;
  asset_type: string;
  status: string;
  commissioned_at: string | null;
  notes: string;
  data_source: DataSource;
  zone_code?: string | null;
  zone_name?: string | null;
};

export type PlantItem = {
  id: string;
  zone_id: string;
  crop_name: string;
  variety: string;
  planted_at: string;
  expected_harvest: string | null;
  growth_stage: string;
  plant_count: number;
  health_status: string;
  notes: string;
  data_source: DataSource;
  zone_code?: string | null;
  moisture_pct?: number | null;
  risk_level?: RiskLevel | null;
};

export type IrrigationItem = {
  id: string;
  zone_id: string;
  name: string;
  method: string;
  valve_code: string;
  status: string;
  last_run_at: string | null;
  next_window: string | null;
  budget_m3: number;
  used_m3: number;
  recommendation: string;
  recommendation_mm: number | null;
  data_source: DataSource;
  zone_code?: string | null;
  moisture_pct?: number | null;
  control_enabled?: boolean;
  control_note?: string;
};

export type TaskItem = {
  id: string;
  title: string;
  task_type: string;
  zone_id: string | null;
  assignee: string;
  priority: TaskPriority;
  status: TaskStatus;
  due_at: string | null;
  origin: string;
  notes: string;
  data_source: DataSource;
  zone_code?: string | null;
};

export type DeviceItem = {
  id: string;
  zone_id: string | null;
  name: string;
  device_type: string;
  vendor: string;
  status: string;
  metric: string | null;
  last_value: string | null;
  unit: string | null;
  last_seen_at: string | null;
  binding_note: string;
  data_source: DataSource;
  zone_code?: string | null;
  live?: boolean;
  status_label?: string;
  readings?: SensorReading[];
};

export type SensorReading = {
  id: string;
  device_id: string;
  metric: string;
  value: number;
  unit: string;
  recorded_at: string;
  data_source: DataSource;
};

export type AgentItem = {
  id: string;
  name: string;
  role: string;
  status: string;
  description: string;
  last_run_at: string | null;
  controls_hardware: boolean;
  data_source: DataSource;
  runs?: AgentRun[];
};

export type AgentRun = {
  id: string;
  agent_id: string;
  summary: string;
  recommendation: string;
  created_at: string;
  data_source: DataSource;
};

export type DiagnosisItem = {
  id: string;
  zone_id: string | null;
  plant_id: string | null;
  title: string;
  symptom: string;
  conclusion: string;
  confidence: number;
  severity: RiskLevel;
  created_at: string;
  data_source: DataSource;
  zone_code?: string | null;
};

export type AIJobItem = {
  id: string;
  title: string;
  job_type: string;
  status: string;
  input_summary: string;
  output_summary: string;
  created_at: string;
  data_source: DataSource;
  controls_hardware: boolean;
};

export type RobotItem = {
  id: string;
  name: string;
  robot_type: string;
  status: string;
  capability_boundary: string;
  last_pose: string | null;
  control_enabled: boolean;
  data_source: DataSource;
  live_gps?: boolean;
  stub?: boolean;
};

export type FleetItem = {
  id: string;
  name: string;
  vehicle_type: string;
  status: string;
  operator: string;
  last_service: string | null;
  last_known_place: string;
  notes: string;
  data_source: DataSource;
  live_gps?: boolean;
  location_note?: string;
};

export type LotItem = {
  id: string;
  crop_name: string;
  quantity_kg: number;
  grade: string;
  location: string;
  harvested_at: string;
  destination: string;
  notes: string;
  data_source: DataSource;
};

export type VendorItem = {
  id: string;
  name: string;
  category: string;
  contact: string;
  phone: string;
  rating: string;
  notes: string;
  data_source: DataSource;
};

export type NoteItem = {
  id: string;
  author: string;
  role: string;
  title: string;
  body: string;
  related_module: string;
  created_at: string;
  data_source: DataSource;
};

export type Architecture = {
  product: string;
  farm: string;
  stack: { web: string; api: string; db: string };
  modules: Record<string, string[]>;
  boundaries: string[];
  data_sources: DataSource[];
  generated_at: string;
};

export type Workbench = {
  title: string;
  focus_date: string;
  blocks: { id: string; title: string; items: Record<string, unknown>[] }[];
};

export type TaskCreateInput = {
  title: string;
  task_type?: string;
  zone_id?: string | null;
  assignee?: string;
  priority?: TaskPriority;
  due_at?: string | null;
  notes?: string;
  origin?: string;
  data_source?: DataSource;
};

export type TaskPatchInput = {
  status?: TaskStatus;
  assignee?: string;
  notes?: string;
  priority?: TaskPriority;
};

export type DiagnosisCreateInput = {
  zone_id?: string | null;
  plant_id?: string | null;
  title: string;
  symptom: string;
  conclusion?: string;
  confidence?: number;
  severity?: RiskLevel;
  data_source?: DataSource;
};

export type AIJobCreateInput = {
  title: string;
  job_type?: string;
  input_summary?: string;
};

export type NoteCreateInput = {
  author: string;
  role?: string;
  title: string;
  body: string;
  related_module?: string;
};

export type RobotCommandInput = {
  command: string;
  args?: Record<string, unknown>;
};
