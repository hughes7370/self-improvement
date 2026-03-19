# OpenAI SDK Integration

Reference for running self-improvement cycles on agents built with the OpenAI SDK
(including Codex CLI, Responses API, and Assistants API).

## Agent Skills in OpenAI / Codex

OpenAI Codex discovers skills from `.agents/skills/` directories. Skills use the same
SKILL.md format as this one. The self-improvement skill can be installed alongside any
Codex agent and invoked with `$self-improvement` or by describing an improvement task.

### Skill Discovery

Codex scans `.agents/skills/` in every directory from CWD to repo root. To install:

```bash
mkdir -p .agents/skills/self-improvement
cp -r self-improvement/* .agents/skills/self-improvement/
```

Codex loads metadata (name + description) at startup, full SKILL.md on activation.

## Evaluation with the OpenAI Evals Framework

OpenAI provides a structured evals system. Use it for the **Assess** step:

### Defining Evals

```python
from openai import OpenAI

client = OpenAI()

# Run a batch of test cases through the agent
results = []
for test_case in test_suite:
    response = client.responses.create(
        model="gpt-4.1",
        input=test_case["input"],
        tools=agent_tools,
        instructions=agent_system_prompt,
    )
    results.append({
        "input": test_case["input"],
        "expected": test_case["expected"],
        "actual": response.output_text,
        "tokens": response.usage.total_tokens,
        "latency_ms": response.usage.completion_time_ms,
    })
```

### Structured Outputs for Evaluation

Use structured outputs to force consistent grading:

```python
from pydantic import BaseModel

class EvalResult(BaseModel):
    accuracy_score: float  # 0-1
    completeness_score: float  # 0-1
    issues_found: list[str]
    improvement_suggestions: list[str]

# Use the model as its own judge
eval_response = client.responses.create(
    model="gpt-4.1",
    input=f"""Evaluate this agent output against the expected result.

Input: {test_case['input']}
Expected: {test_case['expected']}
Actual: {result['actual']}

Score accuracy and completeness from 0-1. List issues and suggestions.""",
    text={"format": {"type": "json_schema", "json_schema": EvalResult.model_json_schema()}},
)
```

## Reflexion Implementation

### Reflection Storage

Store reflections as structured JSON alongside the agent config:

```python
import json
from pathlib import Path

REFLECTIONS_PATH = Path(".agents/reflections/")

def write_reflection(run_id: str, task: str, outcome: str,
                     failure_mode: str, root_cause: str, lesson: str):
    reflection = {
        "run_id": run_id,
        "task": task,
        "outcome": outcome,
        "failure_mode": failure_mode,
        "root_cause": root_cause,
        "lesson": lesson,
        "timestamp": datetime.now().isoformat(),
    }
    path = REFLECTIONS_PATH / f"{run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reflection, indent=2))
    return reflection

def load_recent_reflections(n: int = 10) -> list[dict]:
    files = sorted(REFLECTIONS_PATH.glob("*.json"), reverse=True)[:n]
    return [json.loads(f.read_text()) for f in files]
```

### Injecting Reflections into Context

Append recent reflections to the system prompt before each run:

```python
reflections = load_recent_reflections(5)
reflection_block = "\n".join(
    f"- [{r['run_id']}] {r['lesson']}" for r in reflections
)

system_prompt = f"""{base_system_prompt}

## Lessons from Recent Runs
{reflection_block}
"""
```

## Shadow Testing

Use the Responses API to run parallel evaluations:

```python
async def shadow_test(test_cases, current_prompt, proposed_prompt):
    current_results = []
    proposed_results = []

    for case in test_cases:
        # Run current version
        current = client.responses.create(
            model="gpt-4.1",
            input=case["input"],
            instructions=current_prompt,
        )
        # Run proposed version
        proposed = client.responses.create(
            model="gpt-4.1",
            input=case["input"],
            instructions=proposed_prompt,
        )
        current_results.append(current)
        proposed_results.append(proposed)

    return compare_results(current_results, proposed_results, test_cases)
```

## Meta-Log Storage

For Codex agents, store the meta-log in the repo alongside agent config:

```
.agents/
├── skills/
│   └── self-improvement/
├── reflections/
│   ├── run-001.json
│   └── run-002.json
├── meta-log/
│   ├── cycle-001.json
│   └── summary.md
└── snapshots/
    ├── v1/  (prompt + config backup before cycle 1)
    └── v2/
```

## Versioning and Rollback

Snapshot the agent state before each change:

```python
import shutil

def snapshot_agent_state(cycle_number: int):
    snapshot_dir = Path(f".agents/snapshots/v{cycle_number}")
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    # Copy all agent config files
    for config_file in [".agents/instructions.md", ".agents/tools.json"]:
        if Path(config_file).exists():
            shutil.copy2(config_file, snapshot_dir)
    # Copy all skill files
    if Path(".agents/skills").exists():
        shutil.copytree(".agents/skills", snapshot_dir / "skills",
                        dirs_exist_ok=True)

def rollback_to(cycle_number: int):
    snapshot_dir = Path(f".agents/snapshots/v{cycle_number}")
    for item in snapshot_dir.iterdir():
        target = Path(".agents") / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)
```
