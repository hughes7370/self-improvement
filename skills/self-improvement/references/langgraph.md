# LangGraph Integration

Reference for running self-improvement cycles on agents built with LangGraph.

## Why LangGraph Fits

LangGraph's graph-based execution with support for **cycles** makes it a natural fit for
self-improvement. The generate → reflect → revise loop maps directly to LangGraph nodes
and conditional edges. Unlike linear pipelines, LangGraph can implement iterative
reflection loops that persist until quality criteria are met.

## Architecture: The Reflection Graph

The core self-improvement pattern in LangGraph is a state machine with three node types:

```
[Generator] → [Critic/Reflector] → [Revisor]
     ↑                                  |
     └──────── (if not passing) ────────┘
```

### Basic Reflection Agent

```python
from langgraph.graph import StateGraph, MessagesState, END

def generator_node(state: MessagesState):
    """Generate or regenerate the agent's output."""
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

def reflection_node(state: MessagesState):
    """Evaluate the output and provide structured critique."""
    critique_prompt = f"""Evaluate this agent output against the criteria:
    - Accuracy: Does it correctly address the task?
    - Completeness: Are all requirements met?
    - Efficiency: Is the approach optimal?

    If all criteria score above 0.8, respond with APPROVED.
    Otherwise, provide specific, actionable feedback for improvement."""

    critique = llm.invoke([
        {"role": "system", "content": critique_prompt},
        *state["messages"]
    ])
    return {"messages": [critique]}

def should_continue(state: MessagesState) -> str:
    last_message = state["messages"][-1].content
    if "APPROVED" in last_message or len(state["messages"]) > 6:
        return END
    return "generator"

# Build the graph
builder = StateGraph(MessagesState)
builder.add_node("generator", generator_node)
builder.add_node("reflector", reflection_node)
builder.set_entry_point("generator")
builder.add_edge("generator", "reflector")
builder.add_conditional_edges("reflector", should_continue)
graph = builder.compile()
```

### Using langgraph-reflection (Prebuilt)

LangGraph provides a prebuilt reflection graph via `langgraph-reflection`:

```python
from langgraph_reflection import create_reflection_graph

# Your main agent graph
assistant_graph = build_my_agent()

# A judge that evaluates the agent's output
def judge_response(state, config):
    evaluator = create_llm_as_judge(
        prompt=critique_prompt,
        model="openai:o3-mini",
        feedback_key="pass",
    )
    eval_result = evaluator(
        outputs=state["messages"][-1].content,
        inputs=None,
    )
    if eval_result["score"]:
        return None  # Approved — end loop
    return {
        "messages": [{
            "role": "user",
            "content": eval_result["comment"]
        }]
    }

judge_graph = StateGraph(MessagesState).add_node(judge_response)
reflection_app = create_reflection_graph(assistant_graph, judge_graph)
result = reflection_app.invoke({"messages": user_query})
```

## Implementing the Six-Step Cycle

### Step 1: Assess — Evaluation Node

Add an evaluation node to your existing agent graph:

```python
from typing import TypedDict, Annotated
from langgraph.graph import add_messages

class ImprovementState(TypedDict):
    messages: Annotated[list, add_messages]
    metrics: dict
    reflections: list[dict]
    cycle_number: int
    improvement_vectors: list[dict]

def assess_node(state: ImprovementState):
    """Run evaluation rubric against recent performance."""
    recent_runs = load_recent_runs(n=50)
    metrics = calculate_metrics(recent_runs)
    failures = analyze_failures(recent_runs)
    vectors = rank_improvement_vectors(failures, metrics)

    return {
        "metrics": metrics,
        "improvement_vectors": vectors,
    }
```

### Step 2-3: Identify + Propose

```python
def propose_node(state: ImprovementState):
    """Select highest-impact vector and draft a change proposal."""
    top_vector = state["improvement_vectors"][0]

    proposal_prompt = f"""Based on this improvement vector:
    {json.dumps(top_vector, indent=2)}

    And current metrics:
    {json.dumps(state['metrics'], indent=2)}

    Draft a specific change proposal including:
    - What exactly to change
    - Expected impact on metrics
    - Rollback plan
    - Risk assessment"""

    proposal = llm.invoke(proposal_prompt)
    write_to_meta_log(state["cycle_number"], proposal)
    return {"messages": [proposal]}
```

### Step 4: Test — Shadow Test Node

```python
def shadow_test_node(state: ImprovementState):
    """Run proposed change against baseline in sandbox."""
    proposal = extract_proposal(state["messages"][-1])
    test_cases = load_test_cases()

    baseline_results = run_agent_batch(test_cases, config="current")
    proposed_results = run_agent_batch(test_cases, config=proposal)

    comparison = compare_results(baseline_results, proposed_results)

    if comparison["passes_all_criteria"]:
        return {"messages": [{"role": "system", "content": "SHADOW_TEST_PASSED"}]}
    else:
        return {"messages": [{"role": "system",
                "content": f"SHADOW_TEST_FAILED: {comparison['failures']}"}]}
```

### Wiring the Improvement Graph

```python
builder = StateGraph(ImprovementState)
builder.add_node("assess", assess_node)
builder.add_node("propose", propose_node)
builder.add_node("shadow_test", shadow_test_node)
builder.add_node("deploy", deploy_node)
builder.add_node("measure", measure_node)

builder.set_entry_point("assess")
builder.add_edge("assess", "propose")
builder.add_edge("propose", "shadow_test")

def route_after_test(state):
    last = state["messages"][-1].content
    if "SHADOW_TEST_PASSED" in last:
        return "deploy"
    return "propose"  # Loop back to try a different approach

builder.add_conditional_edges("shadow_test", route_after_test)
builder.add_edge("deploy", "measure")
builder.add_edge("measure", END)

improvement_graph = builder.compile()
```

## Reflexion Pattern in LangGraph

LangGraph's state persistence makes it ideal for maintaining reflective memory:

```python
def reflexion_node(state: ImprovementState):
    """Write a structured reflection after each agent run."""
    last_run = state["messages"][-1]

    reflection = llm.invoke(f"""Review this agent run and write a reflection:
    Task: {state.get('current_task')}
    Output: {last_run.content}
    Errors: {state.get('errors', 'none')}

    Write a JSON reflection with: run_id, outcome, failure_mode,
    root_cause, lesson, inject_into""")

    parsed = json.loads(reflection.content)
    return {"reflections": state.get("reflections", []) + [parsed]}
```

### Persisting Reflections Across Runs

Use LangGraph's checkpointing to persist reflections:

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# Each run uses a thread_id that carries forward reflections
config = {"configurable": {"thread_id": "agent-main"}}
result = graph.invoke(input_state, config)
```

## LangSmith Integration

Use LangSmith for observability — the fuel for self-improvement:

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-key"

# All graph executions are now traced
# Use LangSmith to:
# - Review traces for failure analysis
# - Compare runs before/after changes
# - Track metrics over time
# - Build evaluation datasets from production runs
```

## Multi-Agent Self-Improvement

For complex systems with multiple sub-agents, run improvement cycles per-agent:

```python
# Each sub-agent has its own improvement graph
agents = {
    "search_agent": build_improvement_graph("search"),
    "analysis_agent": build_improvement_graph("analysis"),
    "synthesis_agent": build_improvement_graph("synthesis"),
}

# Orchestrator runs improvement cycles in sequence
for name, improvement_graph in agents.items():
    result = improvement_graph.invoke({
        "cycle_number": current_cycle,
        "messages": [],
        "metrics": load_metrics(name),
    })
```
