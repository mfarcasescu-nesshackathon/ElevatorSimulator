from __future__ import annotations

import argparse
import os
from pathlib import Path

from elevator_sim.bridge import CompositePublisher, DelayPublisher, TcpTickPublisher
from elevator_sim.compare import compare_schedulers
from elevator_sim.config import BuildingConfig, parse_express_flag
from elevator_sim.io import format_stats_text, parse_requests, write_position_log, write_stats
from elevator_sim.schedulers import SCHEDULER_NAMES, get_scheduler
from elevator_sim.simulation import run_simulation


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Discrete-time destination-dispatch elevator simulator"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="Run one scheduler on a request file")
    _add_shared(run_parser)
    run_parser.add_argument(
        "--scheduler",
        default="nearest",
        choices=SCHEDULER_NAMES,
        help="Assignment algorithm (grok sends one API call per timestamp batch)",
    )
    run_parser.add_argument("--live", action="store_true", help="Stream ticks to Blender over TCP")
    run_parser.add_argument("--host", default="127.0.0.1")
    run_parser.add_argument("--port", type=int, default=8765)
    run_parser.add_argument("--wait-client", type=float, default=20.0)
    run_parser.add_argument(
        "--tick-delay",
        type=float,
        default=0.0,
        help="Seconds to wait after each tick (useful for live Blender)",
    )
    run_parser.set_defaults(func=_cmd_run)

    compare_parser = sub.add_parser("compare", help="Run several schedulers on the same input")
    _add_shared(compare_parser)
    compare_parser.add_argument(
        "--include-grok",
        action="store_true",
        help="Also run the Grok batch dispatcher (requires XAI_API_KEY)",
    )
    compare_parser.set_defaults(func=_cmd_compare)

    web_parser = sub.add_parser("web", help="HTTP API for the browser visualizer")
    web_parser.add_argument("--host", default="127.0.0.1")
    web_parser.add_argument("--port", type=int, default=8766)
    web_parser.set_defaults(func=_cmd_web)
    return parser


def _add_shared(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--requests", required=True, help="CSV with header time,id,source,dest")
    parser.add_argument("--elevators", type=int, default=4)
    parser.add_argument("--floors", type=int, default=20)
    parser.add_argument("--capacity", type=int, default=8)
    parser.add_argument(
        "--express",
        action="append",
        default=[],
        help="Express car spec, e.g. 0:1,10,20,30 (repeatable)",
    )
    parser.add_argument("--output-dir", default="outputs")


def _config_from_args(args: argparse.Namespace) -> BuildingConfig:
    express: dict[int, frozenset[int]] = {}
    for spec in args.express:
        elevator_id, floors = parse_express_flag(spec, args.floors)
        express[elevator_id] = floors
    return BuildingConfig(
        num_elevators=args.elevators,
        num_floors=args.floors,
        capacity=args.capacity,
        express_stops=express,
    )


def _cmd_run(args: argparse.Namespace) -> int:
    requests = parse_requests(args.requests)
    config = _config_from_args(args)
    scheduler = get_scheduler(args.scheduler)
    publishers = []
    tcp: TcpTickPublisher | None = None
    if args.live:
        tcp = TcpTickPublisher(host=args.host, port=args.port, wait_client=args.wait_client)
        print(
            f"Waiting up to {args.wait_client:.0f}s for Blender on {args.host}:{args.port} ..."
        )
        tcp.start()
        if tcp._client is None:
            print("No Blender client connected; continuing without live view.")
        else:
            print("Blender client connected.")
        publishers.append(tcp)
    publisher = None
    if publishers:
        publisher = CompositePublisher(publishers)
        if args.tick_delay > 0:
            publisher = DelayPublisher(publisher, args.tick_delay)

    try:
        result = run_simulation(requests, config, scheduler=scheduler, publisher=publisher)
    finally:
        if publisher is not None:
            publisher.close()

    output_dir = Path(args.output_dir)
    write_position_log(output_dir / "positions.csv", result)
    write_stats(output_dir / "stats.txt", result)
    print(format_stats_text(result))
    print(f"Wrote {output_dir / 'positions.csv'} and {output_dir / 'stats.txt'}")
    if args.scheduler == "grok":
        error = getattr(scheduler, "last_error", None)
        print(
            f"Grok API calls={getattr(scheduler, 'api_calls', 0)} "
            f"fallback={getattr(scheduler, 'fallback_calls', 0)}"
            + (f" last_error={error}" if error else "")
        )
        if not os.environ.get("XAI_API_KEY"):
            print("Set XAI_API_KEY to enable Grok; nearest-car was used as fallback.")
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    requests = parse_requests(args.requests)
    config = _config_from_args(args)
    rows = compare_schedulers(
        requests,
        config,
        include_grok=args.include_grok,
        output_dir=args.output_dir,
    )
    for name, result, summary in rows:
        print(
            f"{name:12} ticks={result.ticks:4} "
            f"wait_avg={_fmt(summary['wait']['avg'])} "
            f"total_avg={_fmt(summary['total']['avg'])} "
            f"wait_max={summary['wait']['max']}"
        )
    print(f"Wrote comparison files under {args.output_dir}")
    return 0


def _cmd_web(args: argparse.Namespace) -> int:
    from elevator_sim.server import run_web_server

    run_web_server(host=args.host, port=args.port)
    return 0


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"
