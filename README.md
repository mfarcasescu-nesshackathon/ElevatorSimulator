# Elevator System Simulation

Discrete-time **destination-dispatch** elevator simulator. Passengers give origin and destination when they call; the controller assigns them to a car immediately; destinations do not change.

This repo is a take-home: a Python model with pluggable schedulers (including a Grok batch dispatcher), logs/stats, algorithm comparison, and an optional live Blender view.

## How to run

Python 3.11+. Standard library only for the simulator. Tests need pytest.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the spec sample (51 floors):

```bash
python -m elevator_sim run \
  --requests samples/requests.csv \
  --elevators 4 --floors 51 --capacity 8 \
  --scheduler nearest \
  --output-dir outputs
```

That writes:

- `outputs/positions.csv` — one row per tick, elevator floors
- `outputs/stats.txt` — min/max/avg wait and total times, plus observations

Compare local algorithms on the same demand:

```bash
python -m elevator_sim compare \
  --requests samples/rush_hour.csv \
  --elevators 4 --floors 20 --capacity 8 \
  --output-dir outputs
```

Add `--include-grok` to run the Grok dispatcher too (needs `XAI_API_KEY`).

```bash
python -m pytest
```

### Schedulers

| Name | Flag | Behavior |
|------|------|----------|
| Nearest car | `--scheduler nearest` | Estimate pickup ETA; assign the whole current-time batch greedily |
| Round-robin | `--scheduler round_robin` | Cycle cars that can serve the origin/destination |
| Zone | `--scheduler zone` | Each car owns a contiguous band of origin floors |
| Grok batch | `--scheduler grok` | **One** xAI Chat Completions call per timestamp that has requests |

Grok never sees future rows. If the API is missing, fails, or returns an invalid car, that tick falls back to nearest-car.

```bash
export XAI_API_KEY=...
export GROK_MODEL=grok-4-fast   # optional
python -m elevator_sim run --requests samples/rush_hour.csv --floors 20 --scheduler grok
```

Express cars (bonus): `--express 0:1,10,20` means elevator 0 only stops at those floors. It still travels one floor per tick; it just does not board or alight elsewhere.

### Live Blender UI

Two processes. Start the sim with `--live`, then open Blender:

```bash
python -m elevator_sim run \
  --requests samples/small.csv \
  --floors 8 --elevators 2 --capacity 4 \
  --scheduler nearest \
  --live --tick-delay 0.2
```

```bash
blender --python blender/live_listener.py -- --host 127.0.0.1 --port 8765 --floors 8 --elevators 2
```

Details: [blender/README.md](blender/README.md). The CLI + logs already satisfy the take-home if you skip Blender.

## Time modeling

- One time unit = one floor of travel (up or down).
- The clock always advances one tick at a time, even when the next request is far in the future.
- The scheduler is invoked only for requests whose `time` equals the current tick.

Input CSV:

```
time,id,source,dest
0,passenger1,1,51
0,passenger2,1,37
10,passenger3,20,1
```

`passenger1` and `passenger2` are one Grok (or local) **batch** at t=0. `passenger3` is a later batch at t=10.

## How long you spent

About 8 hours for the core engine, schedulers, Grok batch client, tests, comparison harness, and the live Blender viewer (including setup and write-up).

## Assumptions, simplifications, trade-offs

- Pickup and drop-off are instantaneous on the tick the car is already at that floor (no extra door-dwell).
- Assignment is immediate and sticky. A full car can still own a waiting passenger; they board when space and direction allow.
- Direction is SCAN/LOOK-like: keep serving stops in the current direction, then reverse. Onboard passengers going the current way are boarded; opposite-direction waiters are left for the reverse trip.
- Express cars traverse skipped floors (still one tick each) but do not stop.
- Grok is optional. Local algorithms always run offline and are deterministic.
- Grok output is validated (known passenger ids, legal elevator ids, express constraints). Invalid mappings are replaced per passenger with nearest-car.
- The comparison harness re-runs the **same** request file independently for each scheduler so results are comparable, not a mixed-controller building.

## What I would improve with more time

- Configurable door-dwell and boarding delay so crowded cars cost more than empty ones.
- A true joint batch optimizer for nearest-car (the greedy sequential assignment can pile a timestamp batch onto one car).
- Predicted traffic / lunch-rush weighting, and an explicit fairness penalty in the Grok prompt.
- Smooth interpolation in Blender between ticks, passenger meshes inside the car, and a HUD for wait stats.
- Replay mode from `positions.csv` so the presentation does not depend on a live Grok call.
- Larger generated demand sets and plots of wait-time distributions.

## Presentation notes

`python -m elevator_sim compare --requests samples/rush_hour.csv --floors 20` is the fairness-vs-efficiency walkthrough. Nearest-car (and Grok, when it follows the same goals) usually cuts average wait by grouping riders already on a path. Round-robin is more even on assignment and weaker on position. Zoning is strong for local traffic and weaker for lobby-to-top trips.

Live Blender is the visual for the follow-up meeting: same tick loop, cars moving one floor at a time, waiting passengers as markers at their origin.
