export interface ReleaseTab {
  href: string;
  label: string;
  hint: string;
}

export const RELEASE_TABS: ReleaseTab[] = [
  { href: "/release-1", label: "Release 1", hint: "Nearest-car baseline" },
  { href: "/release-2", label: "Release 2", hint: "Scheduler lab" },
  { href: "/release-3", label: "Release 3", hint: "Rush hours & skipped levels" },
  { href: "/futuristic", label: "Futuristic approach", hint: "MULTI pod network" },
];

export type ClassicRelease = "release1" | "release2" | "release3";
