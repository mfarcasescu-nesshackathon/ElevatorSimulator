"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";
import { Legend, Slider, fmt } from "@/components/controls";
import { IconPeople, IconSpeed } from "@/components/icons";
import {
  POD_COLORS,
  ZONE_ORDER,
  ZONES,
  runMultiSimulation,
  summarizeMulti,
  type MultiRun,
  type ZoneId,
} from "@/lib/multi-sim";

const FuturisticScene = dynamic(
  () => import("@/components/futuristic-scene").then((mod) => mod.FuturisticScene),
  { ssr: false }
);

export function FuturisticLab() {
  const [passengers, setPassengers] = useState(12);
  const [speed, setSpeed] = useState(0.28);
  const [run, setRun] = useState<MultiRun | null>(null);
  const [tick, setTick] = useState(0);
  const [playing, setPlaying] = useState(true);
  const logRef = useRef<HTMLDivElement>(null);

  function handleRun() {
    const next = runMultiSimulation(passengers, 11);
    setRun(next);
    setTick(0);
    setPlaying(true);
  }

  const snapshot = run?.snapshots[Math.min(tick, (run?.snapshots.length ?? 1) - 1)];
  const stats = snapshot ? summarizeMulti(snapshot.done) : null;
  const log = useMemo(() => {
    if (!run) {
      return [];
    }
    const rows: string[] = [];
    for (let index = 0; index <= tick; index += 1) {
      for (const event of run.snapshots[index]?.events ?? []) {
        rows.push(`t${index} ${event}`);
      }
    }
    return rows.slice(-40);
  }, [run, tick]);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [log.length, tick]);

  return (
    <main className="grid min-h-[calc(100vh-3rem)] grid-cols-1 lg:grid-cols-[380px_minmax(0,1fr)]">
      <aside className="max-h-[calc(100vh-3rem)] overflow-y-auto border-b border-slate-800 bg-slate-950/90 p-6 lg:border-b-0 lg:border-r">
        <p className="text-xs uppercase tracking-[0.2em] text-amber-300">Futuristic approach · MULTI</p>
        <h1 className="mt-2 text-2xl font-semibold">Rope-free pod network</h1>
        <p className="mt-2 text-sm text-slate-400">
          Not Floor 0 → 1 → 2 → 3. Pods circulate like a metro: origin node, route through the rotating
          exchange, destination zone. They move vertically, horizontally, and around the hub.
        </p>

        <div className="mt-4 space-y-2 rounded-lg border border-slate-800 bg-slate-900/70 p-3 text-xs text-slate-300">
          <p>
            <span className="text-amber-200">Cabin:</span> carbon-composite pods, several per shaft, no ropes.
          </p>
          <p>
            <span className="text-amber-200">Exchange:</span> rotate at the hub, then cross into another lane.
          </p>
          <p>
            <span className="text-amber-200">Target:</span> 15–30s waits by circulating instead of parking one car per shaft.
          </p>
        </div>

        <div className="mt-6 space-y-5">
          <Slider
            icon={<IconPeople className="h-5 w-5" />}
            label="Riders to generate"
            value={passengers}
            min={4}
            max={12}
            onChange={setPassengers}
          />
          <Slider
            icon={<IconSpeed className="h-5 w-5" />}
            label="Playback speed"
            value={Math.round(speed * 100)}
            min={12}
            max={80}
            display={`${speed.toFixed(2)}s / hop`}
            onChange={(value) => setSpeed(value / 100)}
          />
        </div>

        <div className="mt-6 flex gap-2">
          <button
            className="flex-1 rounded-lg bg-amber-400 px-4 py-2.5 font-medium text-slate-950 hover:bg-amber-300"
            onClick={handleRun}
          >
            Run MULTI network
          </button>
          <button
            className="rounded-lg border border-slate-600 px-4 py-2.5 text-slate-200 hover:bg-slate-800 disabled:opacity-50"
            onClick={() => setPlaying((value) => !value)}
            disabled={!run}
          >
            {playing ? "Pause" : "Play"}
          </button>
        </div>

        <MetroMap snapshot={snapshot} />

        {snapshot ? (
          <div className="mt-4 rounded-xl border border-slate-800 bg-slate-900/70 p-4 text-sm">
            <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Pods in circulation</p>
            <div className="space-y-2">
              {snapshot.pods.map((pod) => (
                <div key={pod.id} className="flex items-center gap-2 text-xs">
                  <span
                    className="inline-block h-3 w-3 rounded-sm"
                    style={{ background: POD_COLORS[pod.id % POD_COLORS.length] }}
                  />
                  <span className="font-medium">Pod {pod.id + 1}</span>
                  <span className="text-slate-400">
                    {ZONES[pod.from].label} → {ZONES[pod.to].label}
                  </span>
                  <span className="ml-auto text-amber-200">
                    {pod.riders.length}/{pod.capacity}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {stats ? (
          <div className="mt-4 rounded-xl border border-slate-800 bg-slate-900/70 p-4 text-sm text-slate-300">
            <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Network summary</p>
            <p>
              Tick {tick} / {Math.max((run?.snapshots.length ?? 1) - 1, 0)}
            </p>
            <p>
              Served {stats.count} · wait {fmt(stats.wait.min)}/{fmt(stats.wait.avg)}/{fmt(stats.wait.max)}
            </p>
            <p>
              Total {fmt(stats.total.min)}/{fmt(stats.total.avg)}/{fmt(stats.total.max)}
            </p>
          </div>
        ) : null}
      </aside>

      <div className="flex min-h-0 flex-col lg:min-h-[calc(100vh-3rem)] lg:overflow-y-auto">
        <section className="relative min-h-[55vh] flex-1 bg-slate-950">
          <FuturisticScene
            snapshots={run?.snapshots ?? []}
            playing={playing}
            secondsPerTick={speed}
            tick={tick}
            onTick={setTick}
          />
          <div className="pointer-events-none absolute bottom-3 left-4 right-4 flex flex-wrap gap-2 text-[11px] text-slate-200">
            <Legend swatch="#f59e0b" label="Rotating exchange" />
            <Legend swatch="#38bdf8" label="Pod cabin" />
            <Legend swatch="#94a3b8" label="Lobby core" />
          </div>
        </section>
        <footer className="border-t border-slate-800 bg-slate-950">
          <div className="flex items-center justify-between px-4 py-2 text-xs uppercase tracking-wide text-slate-500">
            <span>Pod → node → route → destination</span>
            <span>{log.length} events</span>
          </div>
          <div ref={logRef} className="h-44 overflow-y-auto px-4 pb-3">
            {log.length === 0 ? (
              <p className="text-sm text-slate-500">Run the network to see riders request a zone and board a circulating pod.</p>
            ) : (
              <ul className="space-y-1 font-mono text-xs text-slate-300">
                {log.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            )}
          </div>
        </footer>
        {run ? (
          <section className="border-t border-slate-800 px-4 py-4">
            <h2 className="text-xs uppercase tracking-wide text-slate-500">Passenger trips</h2>
            <div className="mt-2 max-h-56 overflow-auto rounded-lg border border-slate-800">
              <table className="min-w-full text-left text-xs">
                <thead className="sticky top-0 bg-slate-900 text-slate-400">
                  <tr>
                    <th className="px-2 py-1.5">Passenger</th>
                    <th className="px-2 py-1.5">Route</th>
                    <th className="px-2 py-1.5">Wait</th>
                    <th className="px-2 py-1.5">Travel</th>
                    <th className="px-2 py-1.5">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {run.passengers.map((person) => {
                    const live =
                      snapshot?.waiting.find((row) => row.id === person.id) ||
                      snapshot?.riding.find((row) => row.id === person.id) ||
                      snapshot?.done.find((row) => row.id === person.id) ||
                      person;
                    return (
                      <tr key={person.id} className="text-slate-200">
                        <td className="px-2 py-1">{person.name}</td>
                        <td className="px-2 py-1 text-slate-400">
                          {person.path.map((node) => ZONES[node].label.replace("Zone ", "")).join(" → ")}
                        </td>
                        <td className="px-2 py-1">{live.wait}</td>
                        <td className="px-2 py-1">{live.travel}</td>
                        <td className="px-2 py-1 text-amber-200">{live.status}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}
      </div>
    </main>
  );
}

function MetroMap({ snapshot }: { snapshot: MultiRun["snapshots"][number] | undefined }) {
  const coords: Record<ZoneId, { x: number; y: number }> = {
    D: { x: 110, y: 22 },
    C: { x: 22, y: 88 },
    hub: { x: 110, y: 88 },
    E: { x: 198, y: 88 },
    B: { x: 110, y: 154 },
    lobby: { x: 110, y: 198 },
  };

  return (
    <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900/70 p-3">
      <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Metro map</p>
      <svg viewBox="0 0 220 220" className="h-56 w-full">
        <polygon points="110,8 210,88 110,168 10,88" fill="#0f172a" stroke="#334155" />
        <line x1="110" y1="168" x2="110" y2="198" stroke="#fbbf24" strokeWidth="3" />
        <line x1="110" y1="22" x2="110" y2="154" stroke="#64748b" strokeWidth="2" />
        <line x1="22" y1="88" x2="198" y2="88" stroke="#64748b" strokeWidth="2" />
        {ZONE_ORDER.map((id) => (
          <g key={id}>
            <circle cx={coords[id].x} cy={coords[id].y} r={id === "hub" ? 8 : 7} fill={ZONES[id].color} />
            <text x={coords[id].x} y={coords[id].y - 12} textAnchor="middle" fill="#cbd5e1" fontSize="8">
              {id === "hub" ? "hub" : id === "lobby" ? "lobby" : `Zone ${id}`}
            </text>
          </g>
        ))}
        {snapshot?.pods.map((pod) => {
          const a = coords[pod.from];
          const b = coords[pod.to];
          const t = pod.progress;
          return (
            <rect
              key={pod.id}
              x={a.x + (b.x - a.x) * t - 5}
              y={a.y + (b.y - a.y) * t - 4}
              width="10"
              height="8"
              rx="2"
              fill={POD_COLORS[pod.id % POD_COLORS.length]}
            />
          );
        })}
      </svg>
    </div>
  );
}
