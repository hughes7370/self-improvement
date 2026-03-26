# Self-Improvement Skill

A framework-agnostic protocol for running structured self-improvement cycles on AI agent systems. Turns any agent from a static tool into a self-optimizing system.

## Installation

Clone the repo, then install for your platform:

```bash
git clone https://github.com/hughes7370/self-improvement.git
cd self-improvement
```

### Claude Code (plugin)

```bash
claude plugin install https://github.com/hughes7370/self-improvement
```

Or manually:

```bash
cp -r skills/self-improvement .claude/skills/
```

### OpenAI Codex

```bash
mkdir -p .agents/skills
cp -r skills/self-improvement .agents/skills/
```

### OpenClaw

```bash
cp -r skills/self-improvement ~/openclaw-workspace/skills/
```

OpenClaw's heartbeat scheduler can trigger improvement cycles automatically — see the [OpenClaw integration guide](skills/self-improvement/references/openclaw.md) for setup.

### LangGraph

LangGraph has no native skill system. Instead, use the reference code directly in your graph:

- [LangGraph integration guide](skills/self-improvement/references/langgraph.md) — reflection nodes, improvement state graphs, LangSmith integration
- [scripts/evaluate.py](skills/self-improvement/scripts/evaluate.py) — import `run_evaluation` and `compare_reports` into your pipeline

## The Cycle

Every self-improvement run follows six steps:

1. **Assess** — Run evaluation rubric against recent performance data
2. **Identify** — Find the highest-impact improvement vector
3. **Propose** — Draft a specific change with expected impact
4. **Test** — Sandbox the change against known-good baselines
5. **Deploy** — Ship with human approval and rollback ready
6. **Measure** — Track post-deployment metrics; rollback if degraded

## Four Improvement Surfaces

| Surface | What Changes | Examples |
|---------|-------------|----------|
| **Memories** | Knowledge referenced at inference | RAG entries, pruning stale data |
| **Prompts** | Instructions across the agent stack | System prompts, tool descriptions |
| **Agent Design** | Architecture and routing logic | Sub-agent patterns, model selection |
| **Infrastructure** | External systems | Data pipelines, tool integrations |

## Framework Support

Works with any agent framework. Integration guides included for:

- **OpenAI SDK / Codex** — [references/openai-sdk.md](skills/self-improvement/references/openai-sdk.md)
- **Anthropic SDK / Claude** — [references/anthropic-sdk.md](skills/self-improvement/references/anthropic-sdk.md)
- **LangGraph** — [references/langgraph.md](skills/self-improvement/references/langgraph.md)
- **OpenClaw** — [references/openclaw.md](skills/self-improvement/references/openclaw.md)

## Repo Structure

```
.claude-plugin/
  plugin.json                     # Plugin manifest
skills/
  self-improvement/
    SKILL.md                      # Full skill protocol
    references/                   # Framework-specific integration guides
    scripts/
      evaluate.py                 # Evaluation harness + report comparison
      meta_log.py                 # Meta-log manager (init, record, rollback-check)
    asset/
      reflection-template.md      # Structured reflection format
      change-proposal-template.md # Change proposal format + approval matrix
      test-suite-template.json    # Test case template
```

## Quick Start

1. Install the plugin (see above)
2. Ask: "Run a self-improvement cycle on this agent"
3. The skill walks through assess → identify → propose → test → deploy → measure

See [SKILL.md](skills/self-improvement/SKILL.md) for the full protocol and detailed instructions.

## License

[MIT](LICENSE)
