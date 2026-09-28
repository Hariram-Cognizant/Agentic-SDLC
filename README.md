# Agentic SDLC

Production-oriented reference implementation of an **Agentic Software Development Life Cycle (SDLC) Framework**. The platform leverages a team of specialized AI agents, Retrieval-Augmented Generation (RAG), Knowledge Graphs, Guardrails, and automated quality evaluation to transform feature requests into traceable, governed, and production-ready software delivery packages.

---

## 🚀 Overview

Agentic SDLC orchestrates an end-to-end software delivery workflow powered by autonomous agents and human approval checkpoints.

The platform combines:

- Multi-Agent Orchestration
- Retrieval-Augmented Generation (RAG)
- Knowledge Graph-Based Reasoning
- Automated Quality Validation
- Security & Compliance Guardrails
- Human-in-the-Loop Governance
- Full Requirement-to-Code Traceability

This enables organizations to accelerate delivery while maintaining enterprise-grade controls, observability, and auditability.

---

# ✨ Key Features

## 🤖 Multi-Agent SDLC Workflow

The framework consists of eleven specialized agents:

| Agent | Responsibility |
|---------|----------------|
| Intake Agent | Captures business requests |
| Context Agent | Retrieves project and domain context |
| Clarification Agent | Generates requirement clarification questions |
| BRD Agent | Produces Business Requirement Documents |
| Story Agent | Generates User Stories and Acceptance Criteria |
| Planning Agent | Creates Technical Design and Implementation Plans |
| Code Agent | Generates code and implementation artifacts |
| Git Agent | Manages branches, commits, and pull requests |
| Review Agent | Performs AI-driven code reviews |
| Sanity Agent | Executes quality and validation checks |
| Release Agent | Prepares release-ready delivery packages |

---

# 🧠 Enterprise AI Enhancements

## 📚 ChromaDB Vector Store

Agentic SDLC uses **ChromaDB** as its vector database for semantic retrieval and long-term project memory.

### Indexed Artifacts

- Business Requirement Documents (BRDs)
- User Stories
- Technical Design Documents
- Coding Standards
- Architecture Decisions
- Previous Releases
- Pull Requests
- Test Reports
- Knowledge Base Articles

### Benefits

- Semantic Search
- Contextual Retrieval
- Historical Knowledge Access
- Requirement Reusability
- Reduced Hallucination Risk

### Retrieval Flow

```text
User Request
      ↓
 Context Agent
      ↓
 ChromaDB Retrieval
      ↓
 Relevant Context
      ↓
 Downstream Agents
```

---

## 🕸️ Neo4j Knowledge Graph

The framework leverages **Neo4j** to model and analyze relationships across requirements, code, architecture, and releases.

### Graph Entities

- Features
- Requirements
- User Stories
- Components
- APIs
- Services
- Developers
- Test Cases
- Releases

### Relationships

```text
Feature
 ├── HAS_REQUIREMENT
 ├── IMPLEMENTED_BY
 ├── TESTED_BY
 ├── DEPENDS_ON
 ├── REVIEWED_BY
 └── RELEASED_IN
```

### Benefits

- End-to-End Traceability
- Dependency Analysis
- Impact Assessment
- Architecture Visualization
- Root Cause Analysis

### Example Neo4j Query

```cypher
MATCH (f:Feature)-[:IMPLEMENTED_BY]->(c:Component)
WHERE f.id = "FEAT-101"
RETURN f,c
```

---

## 📊 RAGAS Quality Evaluation

All AI-generated artifacts can be evaluated using **RAGAS** to ensure retrieval quality and output reliability.

### Evaluation Metrics

| Metric | Description |
|----------|------------|
| Faithfulness | Measures factual grounding |
| Context Precision | Measures retrieval relevance |
| Context Recall | Measures knowledge coverage |
| Answer Relevancy | Measures usefulness |
| Semantic Similarity | Measures alignment with requirements |

### Quality Validation Workflow

```text
Generated Artifact
        ↓
  RAGAS Evaluation
        ↓
 Threshold Validation
        ↓
 Pass / Rework
```

### Sample Configuration

```yaml
ragas:
  faithfulness_threshold: 0.85
  answer_relevancy_threshold: 0.80
  context_precision_threshold: 0.75
```

---

## 🛡️ Guardrails AI

All generated content passes through **Guardrails** before being accepted into the workflow.

### Supported Guardrails

- Hallucination Detection
- Prompt Injection Protection
- JSON Schema Validation
- Output Format Validation
- Architecture 
