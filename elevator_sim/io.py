from __future__ import annotations

import csv
import statistics
from pathlib import Path

from elevator_sim.models import Passenger, Request
from elevator_sim.simulation import SimulationResult


def parse_requests(source: str | Path) -> list[Request]:
    path = Path(source)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(_skip_blank(handle))
        required = {"time", "id", "source", "dest"}
        if reader.fieldnames is None or required - {name.strip() for name in reader.fieldnames}:
            raise ValueError("request CSV must have header time,id,source,dest")
        requests: list[Request] = []
        for row in reader:
            requests.append(
                Request(
                    time=int(row["time"].strip()),
                    id=row["id"].strip(),
                    source=int(row["source"].strip()),
                    dest=int(row["dest"].strip()),
                )
            )
    return requests


def _skip_blank(handle):
    for line in handle:
        if line.strip():
            yield line


def write_position_log(path: str | Path, result: SimulationResult) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = ["t"] + [f"e{index}" for index in range(result.config.num_elevators)]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        for time, floors in enumerate(result.positions):
            writer.writerow([time, *floors])


def summarize_passengers(passengers: list[Passenger]) -> dict:
    if not passengers:
        return {
            "count": 0,
            "wait": {"min": None, "max": None, "avg": None},
            "total": {"min": None, "max": None, "avg": None},
            "travel": {"min": None, "max": None, "avg": None},
        }
    waits = [passenger.wait_time for passenger in passengers if passenger.wait_time is not None]
    totals = [passenger.total_time for passenger in passengers if passenger.total_time is not None]
    travels = [passenger.travel_time for passenger in passengers if passenger.travel_time is not None]
    return {
        "count": len(passengers),
        "wait": _minmaxavg(waits),
        "total": _minmaxavg(totals),
        "travel": _minmaxavg(travels),
    }


def observations(result: SimulationResult) -> list[str]:
    notes: list[str] = []
    summary = summarize_passengers(result.passengers)
    if summary["count"] == 0:
        return ["No passengers were served."]

    wait_avg = summary["wait"]["avg"]
    wait_max = summary["wait"]["max"]
    total_avg = summary["total"]["avg"]
    notes.append(
        f"Served {summary['count']} passengers in {result.ticks} ticks "
        f"with {result.config.num_elevators} elevator(s)."
    )
    if wait_avg and wait_max is not None and wait_max > 3 * wait_avg:
        notes.append(
            f"Wait times are skewed (max {wait_max} vs avg {wait_avg:.1f}); "
            "some passengers waited much longer than the typical rider."
        )
    idle_ratio = _idle_ratio(result)
    notes.append(f"Elevators were idle on {idle_ratio:.0%} of elevator-ticks.")
    if idle_ratio > 0.5 and summary["count"] >= 3:
        notes.append("High idle time suggests the bank is oversized for this demand, or zoning left cars unused.")
    if total_avg is not None:
        notes.append(
            f"Average total time {total_avg:.1f} ticks "
            f"(wait {wait_avg:.1f} + travel {summary['travel']['avg']:.1f})."
        )
    return notes


def write_stats(path: str | Path, result: SimulationResult) -> dict:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = summarize_passengers(result.passengers)
    notes = observations(result)
    lines = [
        f"Scheduler: {result.scheduler_name}",
        f"Elevators: {result.config.num_elevators}",
        f"Floors: {result.config.num_floors}",
        f"Capacity: {result.config.capacity}",
        f"Ticks: {result.ticks}",
        f"Passengers: {summary['count']}",
        "",
        "Wait times",
        f"  min: {summary['wait']['min']}",
        f"  max: {summary['wait']['max']}",
        f"  avg: {_fmt(summary['wait']['avg'])}",
        "",
        "Total times (wait + travel)",
        f"  min: {summary['total']['min']}",
        f"  max: {summary['total']['max']}",
        f"  avg: {_fmt(summary['total']['avg'])}",
        "",
        "Travel times",
        f"  min: {summary['travel']['min']}",
        f"  max: {summary['travel']['max']}",
        f"  avg: {_fmt(summary['travel']['avg'])}",
        "",
        "Observations",
    ]
    lines.extend(f"- {note}" for note in notes)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"summary": summary, "observations": notes}


def format_stats_text(result: SimulationResult) -> str:
    summary = summarize_passengers(result.passengers)
    notes = observations(result)
    parts = [
        f"wait min/max/avg = {summary['wait']['min']}/{summary['wait']['max']}/{_fmt(summary['wait']['avg'])}",
        f"total min/max/avg = {summary['total']['min']}/{summary['total']['max']}/{_fmt(summary['total']['avg'])}",
    ]
    return "; ".join(parts) + "\n" + "\n".join(notes)


def _minmaxavg(values: list[int]) -> dict:
    if not values:
        return {"min": None, "max": None, "avg": None}
    return {
        "min": min(values),
        "max": max(values),
        "avg": statistics.fmean(values),
    }


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"


def _idle_ratio(result: SimulationResult) -> float:
    if len(result.positions) < 2:
        return 1.0
    idle = 0
    total = 0
    for previous, current in zip(result.positions, result.positions[1:]):
        for left, right in zip(previous, current):
            total += 1
            if left == right:
                idle += 1
    return idle / total if total else 1.0
