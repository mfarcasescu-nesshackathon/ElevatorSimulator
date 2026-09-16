"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { RELEASE_TABS } from "@/lib/releases";

export function ReleaseNav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-slate-800 bg-slate-950/95 backdrop-blur">
      <div className="flex flex-wrap items-center gap-1 px-3 py-2 sm:px-5">
        <span className="mr-3 hidden text-[11px] uppercase tracking-[0.18em] text-slate-500 sm:inline">
          Elevator releases
        </span>
        <nav className="flex flex-1 flex-wrap gap-1">
          {RELEASE_TABS.map((tab) => {
            const active = pathname === tab.href || (tab.href === "/release-1" && pathname === "/");
            return (
              <Link
                key={tab.href}
                href={tab.href}
                title={tab.hint}
                className={`rounded-md px-3 py-1.5 text-sm ${
                  active
                    ? "bg-cyan-500/15 text-cyan-200 ring-1 ring-cyan-400/70"
                    : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                }`}
              >
                {tab.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
