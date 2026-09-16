from __future__ import annotations

from pathlib import Path

from elevator_sim.config import BuildingConfig
from elevator_sim.io import observations, summarize_passengers, write_position_log, write_stats
from elevator_sim.models import Request
from elevator_sim.schedulers import get_scheduler
from elevator_sim.simulation import SimulationResult, run_simulation


def compare_schedulers(
    requests: list[Request],
    config: BuildingConfig,
    names: tuple[str, ...] | None = None,
    include_grok: bool = False,
    output_dir: str | Path | None = None,
) -> list[tuple[str, SimulationResult, dict]]:
    selected = list(names) if names else ["nearest", "round_robin", "zone"]
    if include_grok and "grok" not in selected:
        selected.append("grok")

    rows: list[tuple[str, SimulationResult, dict]] = []
    for name in selected:
        scheduler = get_scheduler(name)
        result = run_simulation(list(requests), config, scheduler=scheduler)
        summary = summarize_passengers(result.passengers)
        rows.append((name, result, summary))
        if output_dir is not None:
            directory = Path(output_dir)
            write_position_log(directory / f"positions_{name}.csv", result)
            write_stats(directory / f"stats_{name}.txt", result)

    if output_dir is not None:
        _write_comparison_table(Path(output_dir) / "comparison.md", rows)
    return rows


def _write_comparison_table(path: Path, rows: list[tuple[str, SimulationResult, dict]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Scheduler comparison",
        "",
        "| Scheduler | Ticks | Wait min/avg/max | Total min/avg/max | Idle-ish note |",
        "|-----------|------:|------------------|-------------------|---------------|",
    ]
    for name, result, summary in rows:
        wait = summary["wait"]
        total = summary["total"]
        note = observations(result)[0]
        lines.append(
            f"| {name} | {result.ticks} | "
            f"{wait['min']}/{_fmt(wait['avg'])}/{wait['max']} | "
            f"{total['min']}/{_fmt(total['avg'])}/{total['max']} | {note} |"
        )
    lines.extend(["", "## Fairness vs efficiency", ""])
    lines.extend(_fairness_notes(rows))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _fairness_notes(rows: list[tuple[str, SimulationResult, dict]]) -> list[str]:
    if not rows:
        return []
    by_avg_wait = sorted(rows, key=lambda item: (item[2]["wait"]["avg"] or 0))
    by_max_wait = sorted(rows, key=lambda item: (item[2]["wait"]["max"] or 0))
    by_avg_total = sorted(rows, key=lambda item: (item[2]["total"]["avg"] or 0))
    notes = [
        f"- Lowest average wait: **{by_avg_wait[0][0]}** "
        f"({_fmt(by_avg_wait[0][2]['wait']['avg'])} ticks).",
        f"- Fairest peak wait (lowest max wait): **{by_max_wait[0][0]}** "
        f"(max {by_max_wait[0][2]['wait']['max']}).",
        f"- Lowest average total time: **{by_avg_total[0][0]}** "
        f"({_fmt(by_avg_total[0][2]['total']['avg'])} ticks).",
        "- Zone dispatch tends to be efficient for local traffic and weaker for "
        "cross-zone trips. Round-robin is fairer on assignment but ignores where "
        "cars actually are. Nearest-car (and Grok, when it follows the same goals) "
        "usually cuts wait time by grouping riders already on a car's path.",
    ]
    return notes


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"
