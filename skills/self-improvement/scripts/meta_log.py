#!/usr/bin/env python3
"""
Meta-Log Manager

Manages the self-improvement meta-log — the "change log of changes" that tracks
every improvement cycle so the agent can review the success of its own decisions.

Usage:
    python meta_log.py init <path>           # Initialize meta-log directory
    python meta_log.py record <path>         # Record a new cycle (interactive)
    python meta_log.py summary <path>        # Regenerate summary.md
    python meta_log.py rollback-check <path> # Check if any recent change should be rolled back
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def init_meta_log(base_path: str):
    """Initialize the meta-log directory structure."""
    path = Path(base_path) / "meta-log"
    path.mkdir(parents=True, exist_ok=True)

    summary = path / "summary.md"
    if not summary.exists():
        summary.write_text(
            "# Self-Improvement Meta-Log\n\n"
            "_No cycles recorded yet. Run your first improvement cycle to begin._\n"
        )
    print(f"Meta-log initialized at {path}")


def record_cycle(base_path: str, cycle_data: dict):
    """Record a completed improvement cycle."""
    path = Path(base_path) / "meta-log"
    path.mkdir(parents=True, exist_ok=True)

    cycle_num = cycle_data.get("cycle_number", _next_cycle_number(path))
    cycle_data["cycle_number"] = cycle_num
    cycle_data["recorded_at"] = datetime.now().isoformat()

    filename = path / f"cycle-{cycle_num:03d}.json"
    filename.write_text(json.dumps(cycle_data, indent=2))

    _regenerate_summary(path)
    print(f"Recorded cycle {cycle_num} to {filename}")
    return cycle_num


def check_rollbacks(base_path: str) -> list[dict]:
    """Check recent cycles for changes that should be rolled back."""
    path = Path(base_path) / "meta-log"
    cycles = _load_all_cycles(path)
    flagged = []

    for cycle in cycles:
        if cycle.get("outcome") == "degraded":
            flagged.append({
                "cycle_number": cycle["cycle_number"],
                "change_summary": cycle.get("change_summary", "unknown"),
                "degradation": cycle.get("post_metrics", {}),
                "recommendation": "rollback",
            })
        elif cycle.get("outcome") == "neutral" and cycle.get("effort") == "high":
            flagged.append({
                "cycle_number": cycle["cycle_number"],
                "change_summary": cycle.get("change_summary", "unknown"),
                "recommendation": "consider_reverting",
                "reason": "High-effort change with no measurable impact",
            })

    return flagged


def _next_cycle_number(path: Path) -> int:
    existing = list(path.glob("cycle-*.json"))
    if not existing:
        return 1
    numbers = [int(f.stem.split("-")[1]) for f in existing]
    return max(numbers) + 1


def _load_all_cycles(path: Path) -> list[dict]:
    cycles = []
    for f in sorted(path.glob("cycle-*.json")):
        cycles.append(json.loads(f.read_text()))
    return cycles


def _regenerate_summary(path: Path):
    """Regenerate summary.md from all cycle files."""
    cycles = _load_all_cycles(path)

    lines = ["# Self-Improvement Meta-Log\n"]

    if not cycles:
        lines.append("_No cycles recorded yet._\n")
    else:
        # Stats
        improved = sum(1 for c in cycles if c.get("outcome") == "improved")
        neutral = sum(1 for c in cycles if c.get("outcome") == "neutral")
        degraded = sum(1 for c in cycles if c.get("outcome") == "degraded")
        lines.append(
            f"**{len(cycles)} cycles** | "
            f"{improved} improved | {neutral} neutral | {degraded} degraded\n"
        )

        # Per-cycle entries
        for cycle in reversed(cycles):
            num = cycle.get("cycle_number", "?")
            date = cycle.get("recorded_at", "unknown")[:10]
            change = cycle.get("change_summary", "No description")
            outcome = cycle.get("outcome", "unknown")
            surface = cycle.get("surface", "unknown")

            emoji = {"improved": "+", "neutral": "~", "degraded": "-"}.get(outcome, "?")

            lines.append(f"## Cycle {num} ({date})")
            lines.append(f"- **Surface:** {surface}")
            lines.append(f"- **Change:** {change}")
            lines.append(f"- **Outcome:** [{emoji}] {outcome}")

            if "pre_metrics" in cycle and "post_metrics" in cycle:
                for key in cycle["pre_metrics"]:
                    pre = cycle["pre_metrics"][key]
                    post = cycle["post_metrics"].get(key, pre)
                    lines.append(f"  - {key}: {pre} → {post}")

            if "lessons_learned" in cycle:
                lines.append(f"- **Lesson:** {cycle['lessons_learned']}")

            lines.append("")

    (path / "summary.md").write_text("\n".join(lines))


# --- Cycle data template ---

CYCLE_TEMPLATE = {
    "cycle_number": None,
    "surface": "",  # memories | prompts | agent_design | infrastructure
    "change_summary": "",
    "target": "",
    "current_behavior": "",
    "proposed_change": "",
    "expected_impact": "",
    "rollback_plan": "",
    "risk_assessment": "",
    "pre_metrics": {},
    "post_metrics": {},
    "outcome": "",  # improved | neutral | degraded
    "unexpected_effects": "",
    "lessons_learned": "",
    "exploration": False,  # True if this was an architecture-temperature cycle
}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    base = sys.argv[2]

    if command == "init":
        init_meta_log(base)
    elif command == "summary":
        _regenerate_summary(Path(base) / "meta-log")
        print("Summary regenerated.")
    elif command == "rollback-check":
        flagged = check_rollbacks(base)
        if flagged:
            print(f"Found {len(flagged)} cycles flagged for review:")
            for f in flagged:
                print(f"  Cycle {f['cycle_number']}: {f['recommendation']} — {f['change_summary']}")
        else:
            print("No cycles flagged for rollback.")
    elif command == "record":
        print("Use record_cycle() programmatically with a cycle_data dict.")
        print(f"Template:\n{json.dumps(CYCLE_TEMPLATE, indent=2)}")
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
