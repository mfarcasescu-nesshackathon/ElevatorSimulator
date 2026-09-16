"use client";

import { useEffect, useMemo, useRef } from "react";
import { CAR_COLORS } from "@/lib/events";
import type { SimulationResponse } from "@/lib/types";

export function PositionsLog({
  result,
  tick,
  onSeek,
  variant = "table",
}: {
  result: SimulationResponse;
  tick: number;
  onSeek?: (tick: number) => void;
  variant?: "table" | "board";
}) {
  if (variant === "board") {
    return <PositionsBoard result={result} tick={tick} onSeek={onSeek} />;
  }
  return <PositionsTable result={result} tick={tick} onSeek={onSeek} />;
}

function PositionsBoard({
  result,
  tick,
  onSeek,
}: {
  result: SimulationResponse;
  tick: number;
  onSeek?: (tick: number) => void;
}) {
  const floors = result.config.num_floors;
  const cars = result.config.num_elevators;
  const current = result.positions[Math.min(tick, result.positions.length - 1)] ?? [];
  const previous = tick > 0 ? result.positions[tick - 1] : current;
  const maxTicks = result.positions.length;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="text-xs uppercase tracking-wide text-slate-500">Elevator Positions Log</h2>
          <p className="text-xs text-slate-500">
            Building board at tick {tick}. Click a time cell to scrub playback. Arrows show the last move.
          </p>
        </div>
        <p className="font-mono text-xs text-cyan-300">
          t {tick} / {Math.max(maxTicks - 1, 0)}
        </p>
      </div>

      <div className="grid gap-3 xl:grid-cols-[minmax(280px,360px)_minmax(0,1fr)]">
        <div className="overflow-auto rounded-lg border border-slate-800">
          <table className="min-w-full text-center text-xs">
            <thead className="sticky top-0 bg-slate-900">
              <tr>
                <th className="px-2 py-1.5 text-left text-slate-500">Floor</th>
                {Array.from({ length: cars }, (_, index) => (
                  <th
                    key={index}
                    className="px-2 py-1.5 font-semibold"
                    style={{ color: CAR_COLORS[index % CAR_COLORS.length] }}
                  >
                    E{index + 1}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: floors }, (_, row) => {
                const floor = floors - row;
                return (
                  <tr key={floor} className="border-t border-slate-800/80">
                    <td className="px-2 py-1 text-left font-mono text-slate-500">F{floor}</td>
                    {Array.from({ length: cars }, (_, car) => {
                      const here = current[car] === floor;
                      const move = directionOf(previous[car], current[car]);
                      return (
                        <td key={car} className="px-1 py-1">
                          {here ? (
                            <span
                              className="inline-flex min-w-[3.2rem] items-center justify-center rounded-md px-1.5 py-0.5 font-mono text-[11px] font-semibold text-slate-950"
                              style={{ background: CAR_COLORS[car % CAR_COLORS.length] }}
                            >
                              {move} {floor}
                            </span>
                          ) : (
                            <span className="text-slate-700">·</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <Heatmap result={result} tick={tick} onSeek={onSeek} />
      </div>

      <PositionsTable result={result} tick={tick} onSeek={onSeek} showTitle={false} />
    </div>
  );
}

function Heatmap({
  result,
  tick,
  onSeek,
}: {
  result: SimulationResponse;
  tick: number;
  onSeek?: (tick: number) => void;
}) {
  const cars = result.config.num_elevators;
  const maxFloor = result.config.num_floors;
  const times = result.positions.length;
  const cell = times > 80 ? 8 : times > 40 ? 10 : 12;

  return (
    <div className="rounded-lg border border-slate-800 p-2">
      <p className="mb-2 text-[11px] uppercase tracking-wide text-slate-500">Floor heatmap over time</p>
      <div className="overflow-x-auto">
        <div className="inline-block min-w-full">
          <div className="mb-1 flex font-mono text-[10px] text-slate-500" style={{ paddingLeft: 36 }}>
            {result.positions.map((_, time) =>
              time % 5 === 0 ? (
                <span key={time} className="shrink-0 text-center" style={{ width: cell }}>
                  {time}
                </span>
              ) : (
                <span key={time} className="shrink-0" style={{ width: cell }} />
              )
            )}
          </div>
          {Array.from({ length: cars }, (_, car) => (
            <div key={car} className="mb-1 flex items-center">
              <span
                className="w-9 shrink-0 pr-1 text-right font-mono text-[11px]"
                style={{ color: CAR_COLORS[car % CAR_COLORS.length] }}
              >
                E{car + 1}
              </span>
              {result.positions.map((row, time) => {
                const floor = row[car] ?? 1;
                const active = time === tick;
                const tone = (floor - 1) / Math.max(maxFloor - 1, 1);
                return (
                  <button
                    key={time}
                    type="button"
                    title={`t${time}  E${car + 1} @ F${floor}`}
                    onClick={() => onSeek?.(time)}
                    className={`h-5 shrink-0 ${active ? "ring-1 ring-white" : ""}`}
                    style={{
                      width: cell,
                      background: mix(CAR_COLORS[car % CAR_COLORS.length], tone),
                    }}
                  />
                );
              })}
            </div>
          ))}
        </div>
      </div>
      <p className="mt-2 text-[11px] text-slate-500">Dark = lobby. Bright = top floor. White outline = current tick.</p>
    </div>
  );
}

function PositionsTable({
  result,
  tick,
  onSeek,
  showTitle = true,
}: {
  result: SimulationResponse;
  tick: number;
  onSeek?: (tick: number) => void;
  showTitle?: boolean;
}) {
  const rowRef = useRef<HTMLTableRowElement>(null);
  const elevatorCount = result.config.num_elevators;

  useEffect(() => {
    rowRef.current?.scrollIntoView({ block: "nearest" });
  }, [tick]);

  const moves = useMemo(
    () =>
      result.positions.map((floors, time) => {
        if (time === 0) {
          return floors.map(() => "·" as const);
        }
        return floors.map((floor, index) => directionOf(result.positions[time - 1][index], floor));
      }),
    [result.positions]
  );

  return (
    <div>
      {showTitle ? (
        <>
          <h2 className="text-xs uppercase tracking-wide text-slate-500">Elevator Positions Log</h2>
          <p className="mb-2 text-xs text-slate-500">
            One row per timestamp. Highlighted row is the current playback tick.
          </p>
        </>
      ) : (
        <p className="mb-2 text-[11px] uppercase tracking-wide text-slate-500">Tick table</p>
      )}
      <div className="max-h-72 overflow-auto rounded-lg border border-slate-800">
        <table className="min-w-full text-left font-mono text-xs">
          <thead className="sticky top-0 bg-slate-900 text-slate-400">
            <tr>
              <th className="px-2 py-1.5">t</th>
              {Array.from({ length: elevatorCount }, (_, index) => (
                <th key={index} className="px-2 py-1.5" style={{ color: CAR_COLORS[index % CAR_COLORS.length] }}>
                  e{index} / E{index + 1}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.positions.map((floors, time) => {
              const active = time === tick;
              return (
                <tr
                  key={time}
                  ref={active ? rowRef : undefined}
                  onClick={() => onSeek?.(time)}
                  className={`cursor-pointer ${active ? "bg-cyan-500/20 text-cyan-100" : "text-slate-300 hover:bg-slate-900"}`}
                >
                  <td className="px-2 py-1">{time}</td>
                  {floors.map((floor, index) => (
                    <td key={index} className="px-2 py-1">
                      <span
                        className="mr-1 inline-block w-3 text-center"
                        style={{ color: CAR_COLORS[index % CAR_COLORS.length] }}
                      >
                        {moves[time][index]}
                      </span>
                      {floor}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function directionOf(from: number | undefined, to: number) {
  if (from === undefined || from === to) {
    return "·";
  }
  return to > from ? "↑" : "↓";
}

function mix(hex: string, tone: number) {
  const value = hex.replace("#", "");
  const r = Number.parseInt(value.slice(0, 2), 16);
  const g = Number.parseInt(value.slice(2, 4), 16);
  const b = Number.parseInt(value.slice(4, 6), 16);
  const dark = 18;
  const mixTone = 0.25 + tone * 0.75;
  const rr = Math.round(dark + (r - dark) * mixTone);
  const gg = Math.round(dark + (g - dark) * mixTone);
  const bb = Math.round(dark + (b - dark) * mixTone);
  return `rgb(${rr}, ${gg}, ${bb})`;
}
