---
name: self-improvement
description: >
  Run a structured self-improvement cycle on any agent system — evaluate performance,
  identify improvement vectors, propose changes, test in sandbox, and deploy with rollback.
  Use when the user mentions improving an agent, optimizing prompts, reviewing agent logs,
  self-reflection, reflexion, agent evaluation, agent iteration, performance tuning,
  recursive improvement, agent debugging at a system level, or when the user says
  "improve this agent", "what can we optimize", "run a self-improvement cycle",
  "review agent performance", or "the agent isn't performing well". Also trigger when
  discussing agent maturity, meta-logs, reflective memory, or architecture temperature.
  Works across OpenAI SDK, Anthropic SDK, LangGraph, and OpenClaw.
---

# Self-Improvement Skill

A framework-agnostic protocol for running structured self-improvement cycles on AI agent
systems. This skill turns any agent from a static tool into a self-optimizing system.

## When to Use This Skill

- You want to systematically improve an agent's performance over time
- You need to evaluate an agent against defined metrics and identify improvement vectors
- You want to implement Reflexion-style post-mortem loops
- You're setting up scheduled introspection or A/B testing for agent behavior
- You want to modify prompts, memories, architecture, or infrastructure based on evidence

## Core Concepts

### The Improvement Cycle

Every self-improvement run follows six steps:

1. **Assess** — Run evaluation rubric against recent performance data
2. **Identify** — Find the highest-impact improvement vector
3. **Propose** — Draft a specific change with expected impact; write to meta-log
4. **Test** — Sandbox the change against known-good baselines
5. **Deploy** — If approved (human gate + shadow test), ship the change
6. **Measure** — Track post-deployment metrics; rollback if degradation detected

### The Four Improvement Surfaces

| Surface | What Changes | Examples |
|---------|-------------|----------|
| **Memories** | Knowledge the agent references at inference | RAG entries, kernel memories, pruning stale data |
| **Prompts** | Instructions across the agent stack | System prompts, skill prompts, tool descriptions, persona |
| **Agent Design** | Architecture and routing logic | Sub-agent patterns, decision trees, model selection |
| **Infrastructure** | External systems the agent operates on | Data pipelines, run schedules, tool integrations |

### Maturity Levels

| Level | Name | Description |
|-------|------|-------------|
| 1 | Static | Fixed prompts, fixed tools. No feedback loop. |
| 2 | Reflective | Reviews logs and suggests changes. Human implements. |
| 3 | Recursive | Writes new skills/memories/code. Proposes for human approval. |
| 4 | Autonomous | Modifies own architecture within guardrails. Human reviews periodically. |

Assess which level the target agent currently operates at. The goal of each improvement
cycle is to either improve performance at the current level or advance to the next one.

---

## Step 1: Assess

### Gather Context

Before proposing any changes, collect the following:

1. **Agent description** — What does this agent do? What framework is it built on?
2. **Current metrics** — What does the agent measure today? (success rate, latency, token usage, user satisfaction, error rate)
3. **Recent logs** — Last N runs, errors, edge cases. Ask the user to provide log samples or connect to observability tools.
4. **Existing improvement history** — Has the meta-log been started? Any prior changes?

If the user hasn't defined metrics yet, collaboratively brainstorm North Star metrics:

```
Example metrics by agent type:
- Customer support agent: Resolution rate, escalation rate, avg tokens per resolution
- Data pipeline agent: Accuracy vs ground truth, processing time, retry rate
- Coding agent: Test pass rate, code review acceptance rate, build failures
- Research agent: Factual accuracy score, source diversity, hallucination rate
```

### Run Evaluation

For framework-specific evaluation patterns, see:
- [references/openai-sdk.md](references/openai-sdk.md) — OpenAI SDK / Codex agents
- [references/anthropic-sdk.md](references/anthropic-sdk.md) — Anthropic SDK / Claude agents
- [references/langgraph.md](references/langgraph.md) — LangGraph state machines
- [references/openclaw.md](references/openclaw.md) — OpenClaw workspace agents

The evaluation should produce a structured report:

```json
{
  "timestamp": "2026-03-19T12:00:00Z",
  "cycle_number": 1,
  "metrics": {
    "success_rate": 0.82,
    "avg_tokens": 4200,
    "error_rate": 0.05,
    "user_satisfaction": 0.78
  },
  "failure_analysis": [
    {
      "category": "parsing_error",
      "frequency": 12,
      "sample_ids": ["run-041", "run-067"],
      "root_cause": "Supplier X uses nested tables; agent defaults to Tool A"
    }
  ],
  "improvement_vectors": [
    {
      "surface": "prompts",
      "description": "Add explicit instruction to use Tool B for nested table formats",
      "expected_impact": "+8% success rate on invoice parsing",
      "effort": "low"
    }
  ]
}
```

---

## Step 2: Identify

Rank improvement vectors by **impact / effort ratio**. When multiple vectors are available:

1. Fix failures first (highest error categories)
2. Then optimize (reduce tokens, improve latency)
3. Then explore (try alternative approaches — architecture temperature)

### Architecture Temperature

To prevent local maxima, every 5th cycle (or on user request), force one **exploratory**
change — try a radically different tool, prompt structure, or routing pattern even if
current performance is acceptable. Log the result regardless of outcome.

---

## Step 3: Propose

Every proposed change must include:

```
CHANGE PROPOSAL
===============
Cycle: #N
Surface: [memories | prompts | agent_design | infrastructure]
Target: [specific file, prompt, memory, or component]
Current behavior: [what happens now]
Proposed change: [what will change]
Expected impact: [metric + direction + magnitude]
Rollback plan: [how to revert if it degrades performance]
Risk assessment: [what could go wrong — second/third order effects]
```

Write the proposal to the meta-log before any implementation.

### The Meta-Log

The meta-log is the "change log of changes" — it tracks every improvement cycle so the
agent can review the success of its own past decisions. Structure:

```
meta-log/
├── cycle-001.json
├── cycle-002.json
├── ...
└── summary.md    # Rolling summary of what worked and what didn't
```

Each cycle entry records: proposal, pre-metrics, post-metrics, outcome (improved/neutral/degraded), and lessons learned.

---

## Step 4: Test

### Shadow Testing Protocol

Never deploy a change directly to production. Instead:

1. **Snapshot** the current state (prompts, memories, config) as a versioned backup
2. **Run shadow test** — execute the changed agent on a representative sample of recent inputs alongside the current agent
3. **Compare** outputs against baseline on all tracked metrics (not just the target metric)
4. **Check for second-order effects** — did improving speed degrade accuracy? Did a prompt change break an unrelated workflow?

For framework-specific sandboxing patterns, see the relevant reference file.

### Pass/Fail Criteria

A change passes if:
- Target metric improves by the expected magnitude (±30% tolerance)
- No other tracked metric degrades by more than 5%
- No new error categories are introduced

---

## Step 5: Deploy

### Human-in-the-Loop Gate

**All architectural changes require human approval.** Present the change proposal,
shadow test results, and risk assessment. Wait for explicit approval before deploying.

For Level 2 (Reflective) agents: present findings and let the human implement.
For Level 3+ (Recursive/Autonomous): implement upon approval, with rollback ready.

### Deployment Checklist

- [ ] Meta-log entry written with proposal
- [ ] Snapshot of prior state saved
- [ ] Shadow test passed on all metrics
- [ ] Human approval received
- [ ] Change deployed to production
- [ ] Post-deployment monitoring initiated

---

## Step 6: Measure

After deployment, track the changed metrics over a defined window (minimum 20 runs or
48 hours, whichever is longer).

### Post-Deployment Report

```json
{
  "cycle_number": 1,
  "change_summary": "Added Tool B instruction for nested tables",
  "pre_metrics": { "success_rate": 0.82 },
  "post_metrics": { "success_rate": 0.89 },
  "outcome": "improved",
  "unexpected_effects": "none",
  "lessons_learned": "Explicit tool routing in prompts is more reliable than letting the agent infer tool choice"
}
```

### Rollback Triggers

Automatically flag for rollback if:
- Any tracked metric degrades by more than 10% over the monitoring window
- New error categories appear that weren't present in baseline
- User satisfaction drops (if measured)

Rollback = restore the snapshot from Step 4. One-step. No partial reverts.

---

## Reflexion Pattern

After every failure or suboptimal run (not just during improvement cycles), write a
structured reflection note:

```
REFLECTION
==========
Run ID: [id]
Task: [what was attempted]
Outcome: [success/partial/failure]
What went wrong: [specific failure mode]
Root cause: [why it happened]
Lesson: [actionable insight for future runs]
Inject into: [which prompt/memory should carry this forward]
```

These reflections accumulate in the agent's memory and are injected into future context
windows. They are the primary mechanism for learning between improvement cycles.

**Example:**
```
Run ID: run-067
Task: Parse invoice from Supplier X
Outcome: failure
What went wrong: Agent used Tool A (flat table parser) on nested HTML tables
Root cause: No routing rule distinguishes flat vs nested table formats
Lesson: Supplier X uses nested tables — always route to Tool B
Inject into: invoice-parsing skill prompt, supplier-specific memory
```

---

## Patterns

### 1. Self-Healing (Immediate)

Triggered automatically when a script or pipeline fails.

- **Pipeline level:** Integrate with error monitoring (Sentry, Datadog) → auto-generate fix → deploy PR via GitHub automation
- **Script level:** On failure, capture error + context → write reflection → retry with adjusted approach

### 2. Introspection (Scheduled)

- **Immediate batch:** After every N runs, generate a post-mortem report on the batch
- **Frontier review:** Weekly/monthly deep analysis of logs → identify trends → propose strategic improvements

### 3. Experiments (Periodic)

- **A/B testing:** Maintain 2-3 prompt/tool variants → run in parallel over fixed window → evaluate on quantitative metrics → promote winner
- **Exploration:** Force one novel approach per review cycle (architecture temperature)

---

## Framework Integration

This skill works across any agent framework. For implementation patterns specific to
your stack, read the relevant reference file:

| Framework | Reference | Key Pattern |
|-----------|-----------|-------------|
| OpenAI SDK / Codex | [references/openai-sdk.md](references/openai-sdk.md) | Structured outputs + evals API |
| Anthropic SDK / Claude | [references/anthropic-sdk.md](references/anthropic-sdk.md) | Tool use + message batches |
| LangGraph | [references/langgraph.md](references/langgraph.md) | Reflection nodes + state cycles |
| OpenClaw | [references/openclaw.md](references/openclaw.md) | Heartbeat + workspace skills |

Read the reference file for your framework **before** implementing any cycle steps.

---

## Guardrails

| Risk | Description | Mitigation |
|------|-------------|------------|
| Memory Recall Failure | Memories built but never retrieved | Forced lesson injection at retrieval; periodic recall audits |
| Optimization Silos | Improving one metric while degrading another | Multi-variable scoring; cross-metric regression checks |
| Hallucination Loop | Agent "fixes" with hallucinated logic, creating compounding errors | All changes must pass shadow test against known-good baseline |
| Local Maxima | Agent finds "good enough" and stops exploring | Architecture temperature: force exploration every 5th cycle |
| Slow Degradation | Small reasonable changes compound into performance loss | Versioned snapshots; rolling regression checks; one-step rollback |

---

## Quick Start

If you just want to get started immediately:

1. Ask the user: "What agent are we improving, and what framework is it built on?"
2. Read the relevant framework reference file
3. Ask: "What does good look like? What metrics matter?"
4. Collect recent logs or run a sample batch
5. Run Step 1 (Assess) and present findings
6. Propose the single highest-impact change
7. Test, get approval, deploy, measure

The cycle repeats. Each iteration should take 30-60 minutes for a well-instrumented agent.
