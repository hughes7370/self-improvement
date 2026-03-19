#!/usr/bin/env python3
"""
Self-Improvement Evaluation Runner

Runs a batch of test cases through an agent, collects metrics, and produces
a structured evaluation report. Framework-agnostic — works with any agent
that accepts text input and returns text output.

Usage:
    python evaluate.py --test-suite tests.json --output report.json

Test suite format (tests.json):
[
    {
        "id": "test-001",
        "input": "Parse the invoice from Supplier X",
        "expected": "Extracted line items with totals",
        "tags": ["parsing", "supplier-x"]
    }
]

The agent callable must be provided by the user. This script handles the
evaluation harness, metric calculation, and report generation.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional


def load_test_suite(path: str) -> list[dict]:
    """Load test cases from a JSON file."""
    with open(path) as f:
        return json.load(f)


def run_evaluation(
    test_suite: list[dict],
    agent_fn: Callable[[str], dict],
    judge_fn: Optional[Callable[[dict, dict], dict]] = None,
) -> dict:
    """
    Run evaluation suite and produce a structured report.

    Args:
        test_suite: List of test case dicts with 'id', 'input', 'expected'
        agent_fn: Callable that takes input string and returns
                  {"output": str, "tokens": int, "latency_ms": float}
        judge_fn: Optional callable that takes (test_case, agent_result) and returns
                  {"accuracy": float, "completeness": float, "issues": [str]}

    Returns:
        Structured evaluation report dict
    """
    results = []
    total_tokens = 0
    total_latency = 0
    successes = 0
    failures = []

    for case in test_suite:
        start = time.time()
        try:
            result = agent_fn(case["input"])
            latency = (time.time() - start) * 1000

            entry = {
                "id": case["id"],
                "input": case["input"],
                "expected": case.get("expected", ""),
                "output": result.get("output", ""),
                "tokens": result.get("tokens", 0),
                "latency_ms": latency,
                "error": None,
            }

            if judge_fn:
                grade = judge_fn(case, result)
                entry["grade"] = grade
                if grade.get("accuracy", 0) >= 0.8:
                    successes += 1
                else:
                    failures.append({
                        "id": case["id"],
                        "issues": grade.get("issues", []),
                        "tags": case.get("tags", []),
                    })
            else:
                successes += 1  # No judge = assume success

            total_tokens += entry["tokens"]
            total_latency += latency
            results.append(entry)

        except Exception as e:
            results.append({
                "id": case["id"],
                "input": case["input"],
                "output": None,
                "error": str(e),
                "tokens": 0,
                "latency_ms": 0,
            })
            failures.append({
                "id": case["id"],
                "issues": [f"Exception: {e}"],
                "tags": case.get("tags", []),
            })

    n = len(test_suite)
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_cases": n,
        "metrics": {
            "success_rate": successes / n if n > 0 else 0,
            "error_rate": len(failures) / n if n > 0 else 0,
            "avg_tokens": total_tokens / n if n > 0 else 0,
            "avg_latency_ms": total_latency / n if n > 0 else 0,
        },
        "failures": failures,
        "results": results,
    }

    # Analyze failure categories
    tag_counts = {}
    for f in failures:
        for tag in f.get("tags", ["uncategorized"]):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    report["failure_categories"] = sorted(
        [{"category": k, "count": v} for k, v in tag_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    return report


def compare_reports(baseline: dict, proposed: dict) -> dict:
    """
    Compare two evaluation reports and determine if the proposed version
    passes the shadow test criteria.

    Pass criteria:
    - Target metric improves
    - No other metric degrades by more than 5%
    - No new error categories introduced
    """
    b_metrics = baseline["metrics"]
    p_metrics = proposed["metrics"]

    comparisons = {}
    passes = True

    for key in b_metrics:
        b_val = b_metrics[key]
        p_val = p_metrics[key]
        delta = p_val - b_val

        # For error_rate and latency, lower is better
        if key in ("error_rate", "avg_latency_ms", "avg_tokens"):
            improved = delta < 0
            degraded = delta > (b_val * 0.05) if b_val > 0 else delta > 0
        else:
            improved = delta > 0
            degraded = delta < -(b_val * 0.05) if b_val > 0 else delta < 0

        comparisons[key] = {
            "baseline": round(b_val, 4),
            "proposed": round(p_val, 4),
            "delta": round(delta, 4),
            "improved": improved,
            "degraded": degraded,
        }

        if degraded:
            passes = False

    # Check for new error categories
    baseline_cats = {c["category"] for c in baseline.get("failure_categories", [])}
    proposed_cats = {c["category"] for c in proposed.get("failure_categories", [])}
    new_categories = proposed_cats - baseline_cats

    if new_categories:
        passes = False

    return {
        "passes_all_criteria": passes,
        "comparisons": comparisons,
        "new_error_categories": list(new_categories),
    }


def generate_improvement_vectors(report: dict) -> list[dict]:
    """
    Analyze an evaluation report and generate ranked improvement vectors.
    Returns a list sorted by estimated impact.
    """
    vectors = []

    # Vector from failure categories
    for cat in report.get("failure_categories", []):
        vectors.append({
            "surface": "prompts",
            "description": f"Address {cat['category']} failures ({cat['count']} occurrences)",
            "expected_impact": f"+{min(cat['count'] * 2, 15)}% success rate",
            "effort": "low" if cat["count"] < 5 else "medium",
            "priority": cat["count"],
        })

    # Vector from token usage
    if report["metrics"]["avg_tokens"] > 5000:
        vectors.append({
            "surface": "prompts",
            "description": "Reduce prompt verbosity to lower token usage",
            "expected_impact": f"-{int(report['metrics']['avg_tokens'] * 0.2)} avg tokens",
            "effort": "low",
            "priority": 3,
        })

    # Vector from latency
    if report["metrics"]["avg_latency_ms"] > 10000:
        vectors.append({
            "surface": "agent_design",
            "description": "Optimize tool call chain to reduce latency",
            "expected_impact": f"-{int(report['metrics']['avg_latency_ms'] * 0.15)}ms avg latency",
            "effort": "medium",
            "priority": 2,
        })

    return sorted(vectors, key=lambda v: v["priority"], reverse=True)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python evaluate.py --test-suite tests.json --output report.json")
        print("\nThis script provides the evaluation harness. Import and use")
        print("run_evaluation() with your own agent_fn and judge_fn callables.")
        sys.exit(1)

    # Parse args
    test_path = sys.argv[sys.argv.index("--test-suite") + 1]
    output_path = sys.argv[sys.argv.index("--output") + 1]

    suite = load_test_suite(test_path)
    print(f"Loaded {len(suite)} test cases from {test_path}")
    print("Note: Provide agent_fn and judge_fn by importing this module.")
    print("Run: from evaluate import run_evaluation, compare_reports")
