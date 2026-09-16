import type { ReactNode } from "react";

export function Slider({
  icon,
  label,
  value,
  min,
  max,
  display,
  onChange,
}: {
  icon: ReactNode;
  label: string;
  value: number;
  min: number;
  max: number;
  display?: string;
  onChange: (value: number) => void;
}) {
  return (
    <label className="block text-sm">
      <span className="mb-1 flex items-center justify-between text-slate-300">
        <span className="flex items-center gap-2">
          <span className="text-cyan-400">{icon}</span>
          {label}
        </span>
        <span className="font-mono text-cyan-300">{display ?? value}</span>
      </span>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="w-full accent-cyan-400"
      />
    </label>
  );
}

export function Legend({ swatch, label }: { swatch: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-950/70 px-2 py-1">
      <span className="h-2.5 w-2.5 rounded-full" style={{ background: swatch }} />
      {label}
    </span>
  );
}

export function fmt(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "n/a";
  }
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}
