# Change Proposal Template

Use this template when proposing any modification through the self-improvement cycle.
Every proposed change must be documented before implementation.

## Template

```json
{
  "cycle_number": null,
  "timestamp": "<ISO 8601>",
  "surface": "<memories | prompts | agent_design | infrastructure>",
  "target": "<specific file, prompt, memory, or component being changed>",
  "current_behavior": "<what happens now — be specific>",
  "proposed_change": "<what will change — include exact diffs where possible>",
  "expected_impact": {
    "metric": "<which metric improves>",
    "direction": "<increase | decrease>",
    "magnitude": "<estimated change, e.g. '+8%' or '-500 tokens'>",
    "confidence": "<low | medium | high>"
  },
  "rollback_plan": "<how to revert — ideally 'restore snapshot vN'>",
  "risk_assessment": {
    "second_order_effects": "<what else might change>",
    "worst_case": "<what happens if this goes badly wrong>",
    "mitigation": "<how worst case is prevented or detected>"
  },
  "exploration": false,
  "approval_required": true,
  "approved_by": null,
  "approved_at": null
}
```

## Approval Matrix

| Change Type | Approval Required | Who Approves |
|-------------|------------------|--------------|
| Add reflection to memory | No | Self |
| Modify reference file | No | Self |
| Adjust prompt wording (minor) | Yes — lightweight | Human (async) |
| Change tool routing logic | Yes — full review | Human (sync) |
| Modify agent architecture | Yes — full review | Human (sync) |
| Change model selection | Yes — full review | Human (sync) |
| Modify data pipeline | Yes — full review | Human (sync) |
| Add or remove a tool | Yes — full review | Human (sync) |

## Shadow Test Checklist

Before any approved change goes live:

- [ ] Baseline snapshot saved (prompt state, config, metrics)
- [ ] Proposed change applied to shadow/test environment
- [ ] Representative test cases run on both baseline and proposed
- [ ] All tracked metrics compared (not just the target metric)
- [ ] No metric degraded by more than 5%
- [ ] No new error categories introduced
- [ ] Results documented in meta-log
