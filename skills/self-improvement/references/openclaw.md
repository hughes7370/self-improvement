# OpenClaw Integration

Reference for running self-improvement cycles on agents built with OpenClaw.

## Why OpenClaw Fits

OpenClaw is uniquely suited for self-improvement because of three features:

1. **Persistent daemon** — The agent runs continuously, accumulating state across sessions
2. **Heartbeat scheduler** — Built-in cron-like system for scheduled introspection
3. **Workspace skills** — Markdown-based skills that the agent can read and write to disk

Unlike session-based agents, OpenClaw maintains memory and context between runs, making
it a natural platform for recursive self-improvement loops.

## Skill Installation

OpenClaw discovers skills from the workspace directory. Install the self-improvement
skill:

```bash
# Copy to workspace skills directory
cp -r self-improvement/ ~/openclaw-workspace/skills/self-improvement/

# Or use ClawHub (if available)
openclaw skill install self-improvement
```

OpenClaw loads skill metadata at startup. The full SKILL.md is loaded when the agent
decides to use the skill (e.g., when asked to "improve yourself" or during scheduled
introspection).

## Heartbeat-Driven Introspection

OpenClaw's heartbeat is the key mechanism for scheduled self-improvement. Configure
the HEARTBEAT.md in your workspace to include introspection tasks:

```markdown
# Heartbeat Checklist

- [ ] Check if any recent runs had errors — if so, write a reflection
- [ ] Every Monday at 9am: Run a full self-improvement cycle (assess, identify, propose)
- [ ] Every 50 runs: Compare current metrics against baseline and flag degradation
- [ ] If a reflection mentions the same failure mode 3+ times: auto-propose a fix
```

The gateway triggers the heartbeat at configurable intervals (default 30 minutes). On
each heartbeat, the agent reads HEARTBEAT.md, decides if any item requires action, and
either executes or responds with HEARTBEAT_OK.

### Scheduling Improvement Cycles

For time-based scheduling, use the heartbeat with date checks:

```markdown
- [ ] If today is Monday and no improvement cycle has run this week:
      Load the self-improvement skill and run a full Assess → Propose cycle.
      Save results to meta-log/cycle-{date}.json.
```

For event-based scheduling, use error monitoring:

```markdown
- [ ] If error_count in the last 24 hours > 5:
      Load the self-improvement skill and run an immediate assessment.
      Focus on the highest-frequency error category.
```

## Reflexion in OpenClaw

### Memory-Based Reflections

OpenClaw stores memory as plain Markdown files in the workspace. Reflections integrate
naturally:

```
~/openclaw-workspace/
├── memory/
│   ├── long-term/
│   │   ├── user-preferences.md
│   │   └── lessons-learned.md      ← Reflections accumulate here
│   └── short-term/
├── skills/
│   └── self-improvement/
├── meta-log/
│   ├── cycle-001.json
│   └── summary.md
└── HEARTBEAT.md
```

### Writing Reflections

After any failed or suboptimal task, the agent appends to `lessons-learned.md`:

```markdown
## 2026-03-19: Invoice Parsing Failure

- **Task:** Parse invoice from Supplier X
- **Outcome:** Failed — used flat table parser on nested HTML
- **Lesson:** Supplier X uses nested tables. Always use Tool B for this supplier.
- **Applied to:** invoice-parsing skill prompt (added routing rule)
```

Because OpenClaw memory persists across sessions, these reflections are automatically
available in future runs without explicit injection.

### Forced Lesson Injection

For high-priority lessons that must not be missed, add them to the agent's system
instructions in `openclaw.json`:

```json
{
  "systemPrompt": "...",
  "additionalContext": [
    "memory/long-term/lessons-learned.md"
  ]
}
```

This ensures the reflections are loaded into every conversation, not just when the
memory system retrieves them.

## Shadow Testing via Multi-Agent Routing

OpenClaw supports multi-agent routing — isolated sessions per agent. Use this for
shadow testing:

```json
{
  "agents": {
    "production": {
      "workspace": "~/openclaw-workspace/production/",
      "model": "claude-sonnet-4-20250514"
    },
    "shadow": {
      "workspace": "~/openclaw-workspace/shadow/",
      "model": "claude-sonnet-4-20250514"
    }
  }
}
```

Route test inputs to both agents, compare outputs:

1. Copy the proposed changes to the shadow workspace
2. Send the same inputs to both agents over a test period
3. Compare outputs on tracked metrics
4. If shadow outperforms production, promote the changes

## Meta-Log as Workspace Files

Store the meta-log as plain JSON files in the workspace:

```bash
~/openclaw-workspace/meta-log/
├── cycle-001.json
├── cycle-002.json
└── summary.md
```

The agent can read and write these files directly. The summary.md is a rolling
human-readable digest:

```markdown
# Self-Improvement Summary

## Cycle 1 (2026-03-15)
- **Change:** Added Tool B routing for nested tables
- **Impact:** Success rate 82% → 89%
- **Status:** Kept

## Cycle 2 (2026-03-19)
- **Change:** Reduced system prompt verbosity by 30%
- **Impact:** Tokens per run 4200 → 3100, accuracy unchanged
- **Status:** Kept
```

## Versioning and Rollback

OpenClaw workspaces are plain files — use git for versioning:

```bash
cd ~/openclaw-workspace
git init
git add .
git commit -m "Baseline before improvement cycle 1"

# After each change
git add .
git commit -m "Cycle 1: Added Tool B routing for nested tables"

# Rollback
git revert HEAD  # Undo last change
# or
git checkout <commit-hash> -- skills/ memory/  # Restore specific files
```

This gives you full history, diffing, and one-command rollback — more powerful than
custom snapshot scripts.

## A/B Testing with Channel Routing

OpenClaw's multi-channel support enables natural A/B testing:

```
WhatsApp → Agent A (current prompts)
Telegram → Agent B (proposed prompts)
```

Run both for a fixed period, then compare metrics across channels. This works because
OpenClaw routes different messaging channels to different agent configurations.

## Architecture Temperature

Implement exploration by modifying the heartbeat:

```markdown
- [ ] Every 5th improvement cycle: Try one radically different approach.
      Options: swap to a different model for one sub-task, try a completely
      different tool for the highest-frequency task, restructure the prompt
      from scratch. Log results regardless of outcome.
```

## Self-Modifying Skills

One of OpenClaw's most powerful features for self-improvement: the agent can modify its
own skill files. After an improvement cycle identifies a prompt change:

1. The agent reads the target skill's SKILL.md
2. Modifies the relevant section
3. Writes the updated file back to disk
4. The change takes effect on the next skill activation

**This is Level 3+ (Recursive/Autonomous) behavior.** Gate it behind human approval
unless the agent has been explicitly granted autonomy for specific change types.

```markdown
# In the agent's system instructions:
You may modify your own skill files ONLY for:
- Adding new lessons to reference files
- Updating tool routing rules based on confirmed reflection data
- Adjusting verbosity settings based on user feedback

You must request human approval for:
- Changing core logic or decision trees
- Adding or removing tools
- Modifying system prompts
- Any change that affects multiple skills
```
