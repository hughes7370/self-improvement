# Reflection Template

Use this template after any task that resulted in a failure, partial success, or
suboptimal outcome. The goal is to produce an actionable lesson that prevents the
same issue from recurring.

## Template

```json
{
  "run_id": "<unique identifier for this run>",
  "timestamp": "<ISO 8601 timestamp>",
  "task": "<what was the agent trying to do>",
  "outcome": "<success | partial | failure>",
  "failure_mode": "<specific description of what went wrong>",
  "root_cause": "<why it went wrong — be specific, not generic>",
  "lesson": "<one-sentence actionable takeaway>",
  "inject_into": ["<list of prompts, skills, or memories that should carry this lesson>"],
  "severity": "<low | medium | high | critical>",
  "recurrence_count": 1
}
```

## Guidelines

### Writing Good Lessons

**Bad lessons** (too generic to be actionable):
- "Be more careful with parsing"
- "Check the output format"
- "Handle errors better"

**Good lessons** (specific and actionable):
- "Supplier X uses nested HTML tables — route to Tool B (cheerio parser), not Tool A (flat CSV parser)"
- "When the user asks for 'recent' data, always confirm the date range before querying — 'recent' varies from 1 day to 6 months depending on context"
- "The Stripe API returns paginated results for charges > 100 — always check `has_more` field and loop"

### When to Write Reflections

- **Always write** after: task failure, user correction, unexpected behavior, timeout
- **Consider writing** after: success with high token usage, success that required retries, edge cases that nearly failed
- **Skip** for: routine successes, trivial tasks, tasks already covered by existing reflections

### Recurrence Tracking

If a reflection covers the same failure mode as an existing one, increment
`recurrence_count` on the existing reflection instead of creating a duplicate.
When `recurrence_count` reaches 3, escalate to a formal improvement cycle.

### Injection Strategy

The `inject_into` field determines where this lesson lives. Options:

| Target | When to Use | Persistence |
|--------|-------------|-------------|
| System prompt | Critical lessons that apply to every run | Always loaded |
| Skill prompt | Domain-specific lessons | Loaded when skill activates |
| Memory / RAG | Contextual lessons retrieved by similarity | Retrieved on relevance |
| Tool description | Tool-specific gotchas | Loaded with tool schema |

Prefer the **narrowest scope** that ensures the lesson is available when needed.
A lesson about Supplier X's invoice format belongs in the invoice-parsing skill,
not the global system prompt.
