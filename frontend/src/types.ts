export type GateType = "clarification" | "brd" | "code_plan";

export interface ApprovalGate {
  type: GateType;
  title: string;
  instructions: string;
  required_fields: string[];
  created_at: string;
}

export interface Workflow {
  id: string;
  title: string;
  status: "running" | "awaiting_approval" | "completed" | "failed";
  phase: string;
  source_name: string | null;
  active_gate: ApprovalGate | null;
  approvals: Record<string, Record<string, unknown>>;
  error: string | null;
  created_at: string;
  updated_at: string;
  artifact_count: number;
}

export interface Artifact {
  id: string;
  workflow_id: string;
  type: string;
  name: string;
  content: Record<string, unknown>;
  produced_by: string;
  parent_ids: string[];
  version: number;
  created_at: string;
}
