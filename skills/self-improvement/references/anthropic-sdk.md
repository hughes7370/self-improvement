# Anthropic SDK Integration

Reference for running self-improvement cycles on agents built with the Anthropic SDK
(including Claude Code, Claude Agent SDK, and the Messages API).

## Agent Skills in Claude

Claude discovers skills from multiple locations:
- **Claude Code:** `.claude/skills/` directories, scanned from CWD to repo root
- **Claude.ai:** Uploaded as .skill zip files via Settings > Features
- **Claude API:** Referenced by `skill_id` in the container parameter

### Installation

```bash
# Claude Code
mkdir -p .claude/skills/self-improvement
cp -r self-improvement/* .claude/skills/self-improvement/

# Claude.ai — package and upload
zip -r self-improvement.skill self-improvement/
# Upload via Settings > Features > Custom Skills
```

Claude loads metadata at startup and full SKILL.md when the skill triggers.

## Evaluation with the Messages API

### Batch Evaluation

Use the Message Batches API for running evaluation suites efficiently:

```python
import anthropic

client = anthropic.Anthropic()

# Create evaluation batch
test_requests = []
for i, case in enumerate(test_suite):
    test_requests.append({
        "custom_id": f"eval-{i}",
        "params": {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "system": agent_system_prompt,
            "messages": [{"role": "user", "content": case["input"]}],
            "tools": agent_tools,
        }
    })

batch = client.messages.batches.create(requests=test_requests)
# Poll for completion, then collect results
```

### LLM-as-Judge for Grading

Use a separate Claude call to grade outputs:

```python
def grade_output(test_input, expected, actual):
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system="""You are an evaluation judge. Score the agent output on:
- accuracy (0-1): Does it match the expected result?
- completeness (0-1): Does it cover all required elements?
- efficiency (0-1): Did it use an appropriate amount of reasoning?

Respond with JSON only: {"accuracy": float, "completeness": float,
"efficiency": float, "issues": [str], "suggestions": [str]}""",
        messages=[{
            "role": "user",
            "content": f"Input: {test_input}\nExpected: {expected}\nActual: {actual}"
        }],
    )
    return json.loads(response.content[0].text)
```

## Reflexion Implementation

### Reflection with Tool Use

Claude's tool use makes it natural to structure reflections as tool calls:

```python
reflection_tool = {
    "name": "write_reflection",
    "description": "Record a structured reflection after a task outcome",
    "input_schema": {
        "type": "object",
        "properties": {
            "run_id": {"type": "string"},
            "outcome": {"type": "string", "enum": ["success", "partial", "failure"]},
            "failure_mode": {"type": "string"},
            "root_cause": {"type": "string"},
            "lesson": {"type": "string"},
            "inject_into": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Which prompts or memories should carry this lesson"
            },
        },
        "required": ["run_id", "outcome", "lesson"],
    }
}

# After each agent run, prompt for reflection
reflection_prompt = f"""The agent just completed a task. Review the outcome and
write a reflection using the write_reflection tool.

Task: {task_description}
Result: {task_result}
Errors: {errors if errors else 'None'}

Focus on actionable lessons that would prevent similar issues in future runs."""
```

### Injecting Reflections into Extended Thinking

For Claude models with extended thinking, inject reflections into the system prompt
so they influence the reasoning process:

```python
def build_system_prompt_with_reflections(base_prompt, reflections):
    reflection_block = "\n".join(
        f"- [{r['run_id']}] {r['lesson']}" for r in reflections
    )
    return f"""{base_prompt}

<lessons_from_past_runs>
The following lessons were learned from recent runs. Apply them proactively:
{reflection_block}
</lessons_from_past_runs>"""
```

## Shadow Testing

### Parallel Comparison with Message Batches

```python
async def shadow_test(test_cases, current_config, proposed_config):
    # Build batch with both versions for each test case
    requests = []
    for i, case in enumerate(test_cases):
        # Current version
        requests.append({
            "custom_id": f"current-{i}",
            "params": {
                "model": current_config["model"],
                "max_tokens": 4096,
                "system": current_config["system_prompt"],
                "messages": [{"role": "user", "content": case["input"]}],
            }
        })
        # Proposed version
        requests.append({
            "custom_id": f"proposed-{i}",
            "params": {
                "model": proposed_config["model"],
                "max_tokens": 4096,
                "system": proposed_config["system_prompt"],
                "messages": [{"role": "user", "content": case["input"]}],
            }
        })

    batch = client.messages.batches.create(requests=requests)
    # Collect and compare results by test case
    return compare_paired_results(batch.results, test_cases)
```

## Prompt Stack Management

Claude agents often have a multi-layer prompt stack. The self-improvement cycle can
modify any layer:

```
Layer 1: System prompt (global instructions)
Layer 2: Skill-specific prompts (SKILL.md files)
Layer 3: Tool descriptions (tool.input_schema.description fields)
Layer 4: Memory / RAG context (retrieved at inference)
Layer 5: Reflections (injected lessons from past runs)
```

When proposing a change, specify which layer is being modified. Changes to lower-numbered
layers have broader impact and require more careful testing.

## Versioning in Claude Code

```bash
# Before each improvement cycle, snapshot the agent state
snapshot_dir=".claude/snapshots/cycle-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$snapshot_dir"
cp .claude/settings.json "$snapshot_dir/" 2>/dev/null
cp -r .claude/skills/ "$snapshot_dir/skills/" 2>/dev/null
cp -r .claude/memories/ "$snapshot_dir/memories/" 2>/dev/null

# Rollback
restore_from="$snapshot_dir"
cp "$restore_from/settings.json" .claude/ 2>/dev/null
cp -r "$restore_from/skills/"* .claude/skills/ 2>/dev/null
```

## Claude.ai Specific Notes

When running self-improvement cycles in Claude.ai (rather than Claude Code):

- No filesystem persistence between conversations — use persistent storage API in
  artifacts or export meta-log as downloadable files
- No subagents — run evaluation cases sequentially in conversation
- No CLI tools — skip automated shadow testing; use manual A/B comparison
- Custom skills persist across sessions when uploaded via Settings
- Use the thumbs up/down feedback as a lightweight user satisfaction signal
