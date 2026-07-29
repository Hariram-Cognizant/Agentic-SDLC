import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type { Artifact, Workflow } from "./types";

const stages = ["Intake", "Context", "Clarify", "BRD", "Stories", "Plan", "Code plan", "Implement", "Git", "Review", "Sanity", "Release"];

export default function App() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [error, setError] = useState<string | null>(null);
  const selected = workflows.find((item) => item.id === selectedId) ?? null;

  const refresh = useCallback(async () => {
    try {
      const next = await api.listWorkflows();
      setWorkflows(next);
      setSelectedId((current) => current ?? next[0]?.id ?? null);
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load workflows");
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => {
    if (!selectedId) return setArtifacts([]);
    void api.getArtifacts(selectedId).then(setArtifacts).catch((caught: unknown) =>
      setError(caught instanceof Error ? caught.message : "Unable to load artifacts"),
    );
  }, [selectedId, workflows]);

  async function create(title: string, requirement: string) {
    try {
      const workflow = await api.createWorkflow(title, requirement);
      await refresh();
      setSelectedId(workflow.id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create workflow");
    }
  }

  async function approve(comment: string) {
    if (!selected?.active_gate) return;
    try {
      await api.approve(selected.id, selected.active_gate.type, comment);
      await refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to approve gate");
    }
  }

  return <main>
    <header className="topbar">
      <div className="brand"><div className="mark">A</div><div><strong>Agentic SDLC</strong><span>Delivery control plane</span></div></div>
      <div className="system-state"><i /> Local · traceable · controlled</div>
    </header>
    <section className="hero"><p className="eyebrow">End-to-end feature delivery</p><h1>Turn intent into evidence.</h1><p>Eleven coordinated agents. Three human decisions. One unbroken chain.</p></section>
    {error && <div className="error" role="alert">{error}<button onClick={() => setError(null)}>×</button></div>}
    <section className="workspace">
      <aside>
        <CreateForm onCreate={create} />
        <div className="rail-heading"><span>Runs</span><b>{workflows.length}</b></div>
        <div className="run-list">{!workflows.length && <p className="muted">No runs yet.</p>}
          {workflows.map((workflow) => <button className={`run ${workflow.id === selectedId ? "active" : ""}`} key={workflow.id} onClick={() => setSelectedId(workflow.id)}>
            <span className={`status-dot ${workflow.status}`} /><span><strong>{workflow.title}</strong><small>{label(workflow.phase)}</small></span><time>{relativeTime(workflow.updated_at)}</time>
          </button>)}
        </div>
      </aside>
      <section className="canvas">
        {!selected ? <div className="empty"><span>01</span><h2>Begin with a requirement</h2><p>Create a run to start the traceable delivery workflow.</p></div> : <>
          <div className="run-header"><div><p className="eyebrow">Run {selected.id.slice(0, 8)}</p><h2>{selected.title}</h2></div><span className={`pill ${selected.status}`}>{label(selected.status)}</span></div>
          <Pipeline artifactCount={selected.artifact_count} status={selected.status} />
          {selected.active_gate && <GateCard workflow={selected} onApprove={approve} />}
          {selected.error && <div className="failure"><strong>Execution failed</strong><p>{selected.error}</p></div>}
          <ArtifactGrid artifacts={artifacts} />
        </>}
      </section>
    </section>
  </main>;
}

function CreateForm({ onCreate }: { onCreate: (title: string, requirement: string) => Promise<void> }) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [requirement, setRequirement] = useState("");
  const [submitting, setSubmitting] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); setSubmitting(true); await onCreate(title, requirement);
    setSubmitting(false); setTitle(""); setRequirement(""); setOpen(false);
  }
  if (!open) return <button className="new-run" onClick={() => setOpen(true)}>+ New delivery run</button>;
  return <form className="create-form" onSubmit={submit}>
    <label>Feature name<input required minLength={3} value={title} onChange={(event) => setTitle(event.target.value)} placeholder="e.g. Account recovery" /></label>
    <label>Requirement<textarea required minLength={10} value={requirement} onChange={(event) => setRequirement(event.target.value)} placeholder="Describe actors, intent, constraints, and outcomes…" /></label>
    <div><button type="button" onClick={() => setOpen(false)}>Cancel</button><button className="primary" disabled={submitting}>{submitting ? "Starting…" : "Start run"}</button></div>
  </form>;
}

function Pipeline({ artifactCount, status }: { artifactCount: number; status: Workflow["status"] }) {
  const completed = Math.min(stages.length, status === "completed" ? stages.length : artifactCount);
  return <div className="pipeline">{stages.map((stage, index) =>
    <div className={index < completed ? "done" : index === completed ? "current" : ""} key={stage}><span>{index < completed ? "✓" : index + 1}</span><small>{stage}</small></div>,
  )}</div>;
}

function GateCard({ workflow, onApprove }: { workflow: Workflow; onApprove: (comment: string) => Promise<void> }) {
  const [comment, setComment] = useState(""); const [busy, setBusy] = useState(false); const gate = workflow.active_gate!;
  return <article className="gate-card"><div className="gate-icon">H</div><div><p className="eyebrow">Human decision required</p><h3>{gate.title}</h3><p>{gate.instructions}</p><textarea value={comment} onChange={(event) => setComment(event.target.value)} placeholder="Approval note (optional)" /></div>
    <button className="primary" disabled={busy} onClick={async () => { setBusy(true); await onApprove(comment); setBusy(false); }}>{busy ? "Running agents…" : "Approve & continue"}</button>
  </article>;
}

function ArtifactGrid({ artifacts }: { artifacts: Artifact[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const ordered = useMemo(() => [...artifacts].reverse(), [artifacts]);
  return <section className="artifacts"><div className="section-heading"><div><p className="eyebrow">Evidence trail</p><h3>Generated artifacts</h3></div><span>{artifacts.length} total</span></div>
    <div className="artifact-grid">{ordered.map((artifact) => <article className="artifact" key={artifact.id}>
      <button onClick={() => setExpanded(expanded === artifact.id ? null : artifact.id)}><span className="artifact-index">{artifact.type.slice(0, 2).toUpperCase()}</span><span><strong>{artifact.name}</strong><small>{label(artifact.produced_by)} · v{artifact.version}</small></span><b>{expanded === artifact.id ? "−" : "+"}</b></button>
      {expanded === artifact.id && <pre>{JSON.stringify(artifact.content, null, 2)}</pre>}
    </article>)}</div>
  </section>;
}

function label(value: string) { return value.replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase()); }
function relativeTime(value: string) {
  const seconds = Math.floor((Date.now() - new Date(value).getTime()) / 1000);
  if (seconds < 60) return "now"; if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`; return `${Math.floor(seconds / 86400)}d`;
}
