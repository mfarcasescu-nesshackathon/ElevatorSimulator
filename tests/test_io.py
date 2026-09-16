from pathlib import Path

from elevator_sim.io import parse_requests, summarize_passengers, write_position_log, write_stats
from elevator_sim.schedulers.nearest_car import NearestCarScheduler
from tests.conftest import req, simulate


def test_parse_requests_csv(tmp_path: Path):
    csv_path = tmp_path / "r.csv"
    csv_path.write_text("time,id,source,dest\n0,passenger1,1,5\n2,passenger2,4,1\n", encoding="utf-8")
    requests = parse_requests(csv_path)
    assert [item.id for item in requests] == ["passenger1", "passenger2"]
    assert requests[1].time == 2
    assert requests[1].source == 4


def test_parse_sample_file():
    requests = parse_requests("samples/requests.csv")
    assert len(requests) == 3
    assert requests[0].id == "passenger1"
    assert requests[0].dest == 51


def test_position_log_and_stats(tmp_path: Path):
    result = simulate([req(0, "p", 1, 4)], scheduler=NearestCarScheduler(), num_elevators=2)
    log_path = tmp_path / "positions.csv"
    stats_path = tmp_path / "stats.txt"
    write_position_log(log_path, result)
    write_stats(stats_path, result)
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "t,e0,e1"
    assert lines[1].startswith("0,")
    summary = summarize_passengers(result.passengers)
    assert summary["count"] == 1
    assert summary["wait"]["min"] == 0
    text = stats_path.read_text(encoding="utf-8")
    assert "Wait times" in text
    assert "Total times" in text
