"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  IconBell,
  IconCapacity,
  IconElevator,
  IconFloors,
  IconPeople,
  IconPerson,
  IconRoute,
  IconSpeed,
} from "@/components/icons";
import { PassengerGlyph } from "@/components/passenger-icon";
import { ElevatorReports } from "@/components/reports";
import { Legend, Slider, fmt } from "@/components/controls";
import { runSimulation } from "@/lib/api";
import { CAR_COLORS, collectEvents } from "@/lib/events";
import type { ClassicRelease } from "@/lib/releases";
import type { SimConfig, SimulationResponse } from "@/lib/types";

const ElevatorScene = dynamic(
  () => import("@/components/elevator-scene").then((mod) => mod.ElevatorScene),
  { ssr: false }
);

const SCHEDULERS = [
  { id: "nearest", label: "Nearest car", hint: "Send the closest free-enough car" },
  { id: "round_robin", label: "Round robin", hint: "Rotate cars in order" },
  { id: "zone", label: "Zone-based", hint: "Each car owns a band of floors" },
];

const DEFAULT_CONFIG: SimConfig = {
  elevators: 4,
  floors: 12,
  capacity: 8,
  passengers: 20,
  scheduler: "nearest",
  seed: 1,
};

const COPY: Record<ClassicRelease, { kicker: string; title: string; body: string }> = {
  release1: {
    kicker: "Release 1 · Baseline",
    title: "Nearest-car destination dispatch",
    body: "Today’s working model with a single policy: nearest car. The positions log is the source of truth — one floor per tick, no peek-ahead.",
  },
  release2: {
    kicker: "Release 2 · Scheduler lab",
    title: "Elevator simulator",
    body: "Passengers are named employees or guests. Cyan icons are staff, amber icons are visitors. Compare nearest-car, round-robin, and zone on the same building.",
  },
  release3: {
    kicker: "Release 3 · In progress",
    title: "Rush hours & skipped levels",
    body: "This page matches Release 2 on purpose so we can improve against a frozen baseline. Next: switch policy by traffic mode, and express cars that skip levels.",
  },
};

export function ClassicSimulator({ release }: { release: ClassicRelease }) {
  const lockedNearest = release === "release1";
  const [config, setConfig] = useState<SimConfig>({
    ...DEFAULT_CONFIG,
    scheduler: lockedNearest ? "nearest" : DEFAULT_CONFIG.scheduler,
  });
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [playing, setPlaying] = useState(true);
  const [tick, setTick] = useState(0);
  const [speed, setSpeed] = useState(0.35);
  const copy = COPY[release];

  async function handleRun() {
    setIsLoading(true);
    setError(null);
    try {
      const payload = lockedNearest ? { ...config, scheduler: "nearest" } : config;
      const next = await runSimulation(payload);
      setResult(next);
      setTick(0);
      setPlaying(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not run simulation");
    } finally {
      setIsLoading(false);
    }
  }

  const stats = result?.stats;
  const snapshot = result?.snapshots[Math.min(tick, (result?.snapshots.length ?? 1) - 1)];
  const events = useMemo(
    () => (result ? collectEvents(result.snapshots, tick, 12) : []),
    [result, tick]
  );
  const log = useMemo(
    () => (result ? collectEvents(result.snapshots, tick, 400) : []),
    [result, tick]
  );
  const logRef = useRef<HTMLDivElement>(null);
  const speedLabel = useMemo(() => `${speed.toFixed(2)}s / floor`, [speed]);

  useEffect(() => {
    const node = logRef.current;
    if (node) {
      node.scrollTop = node.scrollHeight;
    }
  }, [log.length, tick]);

  return (
    <main className="grid min-h-[calc(100vh-3rem)] grid-cols-1 lg:grid-cols-[380px_minmax(0,1fr)]">
      <aside className="max-h-[calc(100vh-3rem)] overflow-y-auto border-b border-slate-800 bg-slate-950/90 p-6 lg:border-b-0 lg:border-r">
        <p className="text-xs uppercase tracking-[0.2em] text-cyan-400">{copy.kicker}</p>
        <h1 className="mt-2 text-2xl font-semibold">{copy.title}</h1>
        <p className="mt-2 text-sm text-slate-400">{copy.body}</p>

        {release === "release3" ? (
          <div className="mt-4 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-100">
            Planned here, not wired yet: morning up-peak vs lunch mixed traffic, and skipped-level / express shafts.
            Keep using the Release 2 controls until that lands.
          </div>
        ) : null}

        <div className="mt-6 space-y-5">
          <Slider
            icon={<IconElevator className="h-5 w-5" />}
            label="Elevators"
            value={config.elevators}
            min={1}
            max={10}
            onChange={(elevators) => setConfig({ ...config, elevators })}
          />
          <Slider
            icon={<IconFloors className="h-5 w-5" />}
            label="Floors"
            value={config.floors}
            min={2}
            max={40}
            onChange={(floors) => setConfig({ ...config, floors })}
          />
          <Slider
            icon={<IconCapacity className="h-5 w-5" />}
            label="Max passengers per elevator"
            value={config.capacity}
            min={1}
            max={16}
            onChange={(capacity) => setConfig({ ...config, capacity })}
          />
          <Slider
            icon={<IconPeople className="h-5 w-5" />}
            label="Passengers to generate"
            value={config.passengers}
            min={1}
            max={60}
            onChange={(passengers) => setConfig({ ...config, passengers })}
          />

          {lockedNearest ? (
            <div>
              <span className="mb-2 flex items-center gap-2 text-sm text-slate-300">
                <IconRoute className="h-5 w-5 text-cyan-400" />
                Scheduler
              </span>
              <div className="rounded-lg border border-cyan-400 bg-cyan-500/15 px-3 py-2 text-sm text-cyan-200">
                Nearest car
                <p className="mt-1 text-xs text-slate-400">Locked for Release 1. Other policies live in Release 2.</p>
              </div>
            </div>
          ) : (
            <div>
              <span className="mb-2 flex items-center gap-2 text-sm text-slate-300">
                <IconRoute className="h-5 w-5 text-cyan-400" />
                Scheduler
              </span>
              <div className="grid grid-cols-3 gap-2">
                {SCHEDULERS.map((item) => {
                  const selected = config.scheduler === item.id;
                  return (
                    <button
                      key={item.id}
                      type="button"
                      title={item.hint}
                      onClick={() => setConfig({ ...config, scheduler: item.id })}
                      className={`rounded-lg border px-2 py-2 text-center text-xs ${
                        selected
                          ? "border-cyan-400 bg-cyan-500/15 text-cyan-200"
                          : "border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-500"
                      }`}
                    >
                      {item.label}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          <Slider
            icon={<IconSpeed className="h-5 w-5" />}
            label="Playback speed"
            value={Math.round(speed * 100)}
            min={12}
            max={80}
            display={speedLabel}
            onChange={(value) => setSpeed(value / 100)}
          />
        </div>

        <div className="mt-6 flex gap-2">
          <button
            className="flex-1 rounded-lg bg-cyan-500 px-4 py-2.5 font-medium text-slate-950 hover:bg-cyan-400 disabled:opacity-50"
            onClick={handleRun}
            disabled={isLoading}
          >
            {isLoading ? "Simulating…" : "Run simulation"}
          </button>
          <button
            className="rounded-lg border border-slate-600 px-4 py-2.5 text-slate-200 hover:bg-slate-800 disabled:opacity-50"
            onClick={() => setPlaying((value) => !value)}
            disabled={!result}
          >
            {playing ? "Pause" : "Play"}
          </button>
        </div>
        {error ? <p className="mt-3 text-sm text-rose-400">{error}</p> : null}

        {snapshot ? (
          <div className="mt-6 space-y-3">
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 text-sm">
              <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Cars in motion</p>
              <div className="space-y-2">
                {snapshot.elevators.map((car) => (
                  <div key={car.id} className="flex items-center gap-2">
                    <span
                      className="inline-block h-3 w-3 rounded-sm"
                      style={{ background: CAR_COLORS[car.id % CAR_COLORS.length] }}
                    />
                    <span className="w-8 font-medium">E{car.id + 1}</span>
                    <span className="text-slate-400">F{car.floor}</span>
                    <span className="ml-auto flex items-center gap-1 text-amber-200">
                      <IconPerson className="h-4 w-4" />
                      {car.load}/{car.capacity}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 text-sm">
              <p className="mb-2 flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500">
                <IconBell className="h-4 w-4 text-amber-300" />
                Hall calls right now
              </p>
              {snapshot.waiting.length === 0 ? (
                <p className="text-slate-500">No one is waiting.</p>
              ) : (
                <ul className="space-y-1.5 text-xs">
                  {snapshot.waiting.map((person) => (
                    <li key={person.id} className="flex items-center gap-2">
                      <PassengerGlyph icon={person.icon} role={person.role} size="sm" />
                      <span className="font-medium">{person.name}</span>
                      <span className="text-slate-400">{person.role}</span>
                      <span>
                        {person.floor}→{person.dest}
                      </span>
                      <span className="ml-auto text-cyan-300">
                        {person.is_new ? "requested →" : "waiting at"} E{(person.elevator ?? 0) + 1}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 text-sm">
              <p className="mb-2 flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500">
                Requests & assignments
              </p>
              {events.length === 0 ? (
                <p className="text-slate-500">Waiting for the first hall call…</p>
              ) : (
                <ul className="space-y-1.5 text-xs leading-snug">
                  {events.map((event) => (
                    <li key={event.key} className="flex gap-2">
                      <span className="font-mono text-slate-500">t{event.tick}</span>
                      <span
                        className={
                          event.kind === "request"
                            ? "text-amber-200"
                            : event.kind === "assign"
                              ? "text-cyan-300"
                              : event.kind === "board"
                                ? "text-emerald-300"
                                : "text-slate-300"
                        }
                      >
                        {event.text}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {stats ? (
              <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 text-sm text-slate-300">
                <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Passenger summary</p>
                <p>
                  Tick {tick} / {Math.max((result?.snapshots.length ?? 1) - 1, 0)}
                </p>
                <p>
                  Wait min/avg/max {fmt(stats.wait.min)} / {fmt(stats.wait.avg)} / {fmt(stats.wait.max)}
                </p>
                <p>
                  Total min/avg/max {fmt(stats.total.min)} / {fmt(stats.total.avg)} / {fmt(stats.total.max)}
                </p>
              </div>
            ) : null}
          </div>
        ) : null}
      </aside>

      <div className="flex min-h-0 flex-col lg:min-h-[calc(100vh-3rem)] lg:overflow-y-auto">
        <section className="relative min-h-[55vh] flex-1 bg-slate-950">
          <ElevatorScene
            key={`${result?.config.num_floors}-${result?.config.num_elevators}-${result?.ticks}`}
            snapshots={result?.snapshots ?? []}
            playing={playing}
            secondsPerTick={speed}
            tick={tick}
            onTick={setTick}
          />
          <div className="pointer-events-none absolute bottom-3 left-4 right-4 flex flex-wrap gap-2 text-[11px] text-slate-200">
            <Legend swatch="#22d3ee" label="Employee icon" />
            <Legend swatch="#fbbf24" label="Guest icon" />
            <Legend swatch="#94a3b8" label="Car badge = passengers / capacity" />
          </div>
        </section>
        <footer className="border-t border-slate-800 bg-slate-950">
          <div className="flex items-center justify-between px-4 py-2 text-xs uppercase tracking-wide text-slate-500">
            <span>Passenger request log</span>
            <span>{log.length} events</span>
          </div>
          <div ref={logRef} className="h-44 overflow-y-auto px-4 pb-3">
            {log.length === 0 ? (
              <p className="text-sm text-slate-500">Run a simulation to see named employees and guests request floors.</p>
            ) : (
              <ul className="space-y-1.5">
                {log.map((event) => (
                  <li key={event.key} className="flex items-start gap-2 text-sm">
                    <PassengerGlyph icon={event.icon} role={event.role} size="sm" />
                    <span className="font-mono text-xs text-slate-500">t{event.tick}</span>
                    <span
                      className={
                        event.kind === "request"
                          ? "text-amber-200"
                          : event.kind === "assign"
                            ? "text-cyan-300"
                            : event.kind === "board"
                              ? "text-emerald-300"
                              : "text-slate-300"
                      }
                    >
                      {event.text}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </footer>
        {result ? (
          <ElevatorReports
            result={result}
            tick={tick}
            onSeek={(next) => {
              setTick(next);
              setPlaying(false);
            }}
            positionsVariant={lockedNearest ? "board" : "table"}
          />
        ) : null}
      </div>
    </main>
  );
}
