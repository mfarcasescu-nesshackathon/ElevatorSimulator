"use client";

import { PositionsLog } from "@/components/positions-log";
import { PassengerGlyph } from "@/components/passenger-icon";
import { fmt } from "@/components/controls";
import type { SimulationResponse } from "@/lib/types";

export function ElevatorReports({
  result,
  tick,
  onSeek,
  positionsVariant = "table",
}: {
  result: SimulationResponse;
  tick: number;
  onSeek?: (tick: number) => void;
  positionsVariant?: "table" | "board";
}) {
  const stats = result.stats;
  const stacked = positionsVariant === "board";

  return (
    <section className={`border-t border-slate-800 bg-slate-950 px-4 py-4 ${stacked ? "space-y-4" : "grid gap-4 lg:grid-cols-2"}`}>
      <PositionsLog result={result} tick={tick} onSeek={onSeek} variant={positionsVariant} />

      <div>
        <h2 className="text-xs uppercase tracking-wide text-slate-500">Passenger Summary Statistics</h2>
        <p className="mb-2 text-xs text-slate-500">
          total_time = wait_time + travel_time · {stats.count} passengers served
        </p>
        <div className="grid grid-cols-3 gap-2 text-sm">
          <StatCard title="Wait times" values={stats.wait} />
          <StatCard title="Travel times" values={stats.travel} />
          <StatCard title="Total times" values={stats.total} />
        </div>
        {result.observations.length > 0 ? (
          <ul className="mt-3 space-y-1 text-xs text-slate-400">
            {result.observations.map((note) => (
              <li key={note}>• {note}</li>
            ))}
          </ul>
        ) : null}
        <div className="mt-3 max-h-56 overflow-auto rounded-lg border border-slate-800">
          <table className="min-w-full text-left text-xs">
            <thead className="sticky top-0 bg-slate-900 text-slate-400">
              <tr>
                <th className="px-2 py-1.5">Passenger</th>
                <th className="px-2 py-1.5">Trip</th>
                <th className="px-2 py-1.5">Wait</th>
                <th className="px-2 py-1.5">Travel</th>
                <th className="px-2 py-1.5">Total</th>
              </tr>
            </thead>
            <tbody>
              {result.passengers.map((passenger) => (
                <tr key={passenger.id} className="text-slate-200">
                  <td className="px-2 py-1">
                    <span className="inline-flex items-center gap-1.5">
                      <PassengerGlyph icon={passenger.icon} role={passenger.role} size="sm" />
                      {passenger.name}
                    </span>
                  </td>
                  <td className="px-2 py-1 text-slate-400">
                    {passenger.source}→{passenger.dest}
                  </td>
                  <td className="px-2 py-1">{fmt(passenger.wait_time)}</td>
                  <td className="px-2 py-1">{fmt(passenger.travel_time)}</td>
                  <td className="px-2 py-1">{fmt(passenger.total_time)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function StatCard({
  title,
  values,
}: {
  title: string;
  values: { min: number | null; max: number | null; avg: number | null };
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-3">
      <p className="text-[11px] uppercase tracking-wide text-slate-500">{title}</p>
      <p className="mt-1 text-xs text-slate-400">min / avg / max</p>
      <p className="font-mono text-sm text-cyan-200">
        {fmt(values.min)} / {fmt(values.avg)} / {fmt(values.max)}
      </p>
    </div>
  );
}
