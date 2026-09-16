# Live Blender view

The Python simulator is the source of truth. Blender is a visualization client.

## Run live

Terminal A — start the sim and wait for Blender:

```bash
python -m elevator_sim run \
  --requests samples/small.csv \
  --floors 8 --elevators 2 --capacity 4 \
  --scheduler nearest \
  --live --tick-delay 0.2
```

Terminal B — open Blender with the listener (Blender must be on your `PATH`):

```bash
blender --python blender/live_listener.py -- --host 127.0.0.1 --port 8765 --floors 8 --elevators 4
```

Connect within 20 seconds (override with `--wait-client`). Press Esc in Blender to stop the listener.

Optional: pre-build a `.blend` file:

```bash
blender --background --python blender/create_scene.py -- --floors 20 --elevators 4 --save blender/building.blend
```

Cars jump one floor per tick. Use `--tick-delay` so the motion is visible. Grok dispatch pauses ticks while the API call runs.
