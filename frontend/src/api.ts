import type { Artifact, GateType, Workflow } from "./types";

const API_ROOT = import.meta.env.VITE_API_ROOT ?? "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  listWorkflows: () => request<Workflow[]>("/workflows"),
  createWorkflow: (title: string, requirement: string) =>
    request<Workflow>("/workflows", {
      method: "POST",
      body: JSON.stringify({ title, requirement }),
    }),
  getArtifacts: (workflowId: string) =>
    request<Artifact[]>(`/workflows/${workflowId}/artifacts`),
  approve: (workflowId: string, gate: GateType, comment: string) =>
    request<Workflow>(`/workflows/${workflowId}/approvals`, {
      method: "POST",
      body: JSON.stringify({
        gate,
        approved: true,
        comment,
        answers: {},
        assumptions: [],
        out_of_scope: [],
        success_metrics: [],
      }),
    }),
};
