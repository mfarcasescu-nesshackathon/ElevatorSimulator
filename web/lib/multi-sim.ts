export type ZoneId = "lobby" | "hub" | "B" | "C" | "D" | "E";

export interface Vec3 {
  x: number;
  y: number;
  z: number;
}

export const ZONES: Record<ZoneId, { id: ZoneId; label: string; color: string; position: Vec3 }> = {
  lobby: { id: "lobby", label: "Lobby / core", color: "#94a3b8", position: { x: 0, y: -10, z: 0 } },
  hub: { id: "hub", label: "Rotating exchange", color: "#f59e0b", position: { x: 0, y: 0, z: 0 } },
  B: { id: "B", label: "Zone B", color: "#38bdf8", position: { x: 0, y: -5.2, z: 5.4 } },
  C: { id: "C", label: "Zone C", color: "#34d399", position: { x: -6.2, y: 0, z: 0 } },
  D: { id: "D", label: "Zone D", color: "#c084fc", position: { x: 0, y: 6.2, z: 0 } },
  E: { id: "E", label: "Zone E", color: "#fb7185", position: { x: 6.2, y: 0, z: 0 } },
};

export const ZONE_ORDER: ZoneId[] = ["lobby", "hub", "B", "C", "D", "E"];

const EDGES: Array<[ZoneId, ZoneId]> = [
  ["lobby", "hub"],
  ["hub", "B"],
  ["hub", "C"],
  ["hub", "D"],
  ["hub", "E"],
];

const POD_ROUTES: ZoneId[][] = [
  ["lobby", "hub", "D", "hub", "B", "hub", "lobby"],
  ["lobby", "hub", "C", "hub", "E", "hub", "lobby"],
  ["hub", "D", "hub", "E", "hub", "B", "hub", "C", "hub"],
  ["hub", "C", "hub", "B", "hub", "E", "hub", "D", "hub"],
  ["lobby", "hub", "E", "hub", "lobby"],
  ["lobby", "hub", "D", "hub", "C", "hub", "lobby"],
];

export const POD_COLORS = ["#38bdf8", "#fb7185", "#34d399", "#fbbf24", "#c084fc", "#22d3ee"];

const NAMES = [
  "Ava Chen",
  "Marcus Webb",
  "Priya Nair",
  "Noah Okonkwo",
  "Samira Cole",
  "Elena Rossi",
  "Harper Dane",
  "Kenji Mori",
  "Imani Brooks",
  "Theo Brandt",
  "Maya Patel",
  "Yves Moreau",
];

export interface MultiPassenger {
  id: string;
  name: string;
  origin: ZoneId;
  dest: ZoneId;
  path: ZoneId[];
  pathIndex: number;
  wait: number;
  travel: number;
  status: "waiting" | "riding" | "done";
  podId: number | null;
  requestTick: number;
}

export interface MultiPod {
  id: number;
  route: ZoneId[];
  routeIndex: number;
  progress: number;
  riders: string[];
  capacity: number;
}

export interface MultiSnapshot {
  t: number;
  pods: Array<MultiPod & { position: Vec3; from: ZoneId; to: ZoneId }>;
  waiting: MultiPassenger[];
  riding: MultiPassenger[];
  done: MultiPassenger[];
  events: string[];
}

export interface MultiRun {
  snapshots: MultiSnapshot[];
  passengers: MultiPassenger[];
}

function neighbors(): Map<ZoneId, ZoneId[]> {
  const map = new Map<ZoneId, ZoneId[]>();
  for (const zone of ZONE_ORDER) {
    map.set(zone, []);
  }
  for (const [a, b] of EDGES) {
    map.get(a)?.push(b);
    map.get(b)?.push(a);
  }
  return map;
}

const GRAPH = neighbors();

export function shortestPath(origin: ZoneId, dest: ZoneId): ZoneId[] {
  if (origin === dest) {
    return [origin];
  }
  const queue: ZoneId[] = [origin];
  const prev = new Map<ZoneId, ZoneId>();
  const seen = new Set<ZoneId>([origin]);
  while (queue.length) {
    const node = queue.shift() as ZoneId;
    for (const next of GRAPH.get(node) ?? []) {
      if (seen.has(next)) {
        continue;
      }
      seen.add(next);
      prev.set(next, node);
      if (next === dest) {
        const path = [dest];
        let cursor: ZoneId | undefined = dest;
        while (cursor && cursor !== origin) {
          cursor = prev.get(cursor);
          if (cursor) {
            path.unshift(cursor);
          }
        }
        return path;
      }
      queue.push(next);
    }
  }
  return [origin, dest];
}

function lerp(a: Vec3, b: Vec3, t: number): Vec3 {
  return {
    x: a.x + (b.x - a.x) * t,
    y: a.y + (b.y - a.y) * t,
    z: a.z + (b.z - a.z) * t,
  };
}

function podTarget(pod: MultiPod): { from: ZoneId; to: ZoneId } {
  const from = pod.route[pod.routeIndex];
  const to = pod.route[(pod.routeIndex + 1) % pod.route.length];
  return { from, to };
}

function etaTo(pod: MultiPod, node: ZoneId): number {
  for (let step = 0; step < pod.route.length; step += 1) {
    if (pod.route[(pod.routeIndex + step) % pod.route.length] === node) {
      return step;
    }
  }
  return Number.POSITIVE_INFINITY;
}

function willVisitThen(pod: MultiPod, from: ZoneId, to: ZoneId): boolean {
  const route = pod.route;
  const start = pod.routeIndex;
  let seenFrom = false;
  for (let step = 0; step < route.length * 2; step += 1) {
    const zone = route[(start + step) % route.length];
    if (zone === from) {
      seenFrom = true;
    }
    if (seenFrom && zone === to && !(step === 0 && from === to)) {
      return true;
    }
  }
  return false;
}

function pickPod(pods: MultiPod[], from: ZoneId, to: ZoneId): number | null {
  let best: number | null = null;
  let bestWait = Infinity;
  for (const pod of pods) {
    if (pod.riders.length >= pod.capacity) {
      continue;
    }
    if (!willVisitThen(pod, from, to)) {
      continue;
    }
    const wait = etaTo(pod, from);
    if (wait < bestWait) {
      bestWait = wait;
      best = pod.id;
    }
  }
  return best;
}

export function runMultiSimulation(passengerCount = 12, seed = 7): MultiRun {
  let rng = seed;
  function random() {
    rng = (rng * 1664525 + 1013904223) % 4294967296;
    return rng / 4294967296;
  }
  const destinations = ZONE_ORDER.filter((zone) => zone !== "hub");
  const passengers: MultiPassenger[] = Array.from({ length: passengerCount }, (_, index) => {
    const origin = destinations[Math.floor(random() * destinations.length)];
    let dest = destinations[Math.floor(random() * destinations.length)];
    while (dest === origin) {
      dest = destinations[Math.floor(random() * destinations.length)];
    }
    return {
      id: `m${index + 1}`,
      name: NAMES[index % NAMES.length],
      origin,
      dest,
      path: shortestPath(origin, dest),
      pathIndex: 0,
      wait: 0,
      travel: 0,
      status: "waiting",
      podId: null,
      requestTick: index === 0 ? 0 : Math.floor(index * 1.4),
    };
  });

  const pods: MultiPod[] = POD_ROUTES.map((route, id) => ({
    id,
    route,
    routeIndex: id % route.length,
    progress: 0,
    riders: [],
    capacity: 4,
  }));

  const snapshots: MultiSnapshot[] = [];
  const maxTicks = 90;

  function currentNode(person: MultiPassenger): ZoneId {
    return person.path[person.pathIndex] ?? person.origin;
  }

  function nextHop(person: MultiPassenger): ZoneId | null {
    return person.path[person.pathIndex + 1] ?? null;
  }

  for (let t = 0; t <= maxTicks; t += 1) {
    const events: string[] = [];

    for (const person of passengers) {
      if (person.status !== "waiting" || person.requestTick > t) {
        continue;
      }
      const hop = nextHop(person);
      if (!hop) {
        continue;
      }
      const assigned = pickPod(pods, currentNode(person), hop);
      if (person.requestTick === t) {
        person.podId = assigned;
        events.push(
          `${person.name} requested ${ZONES[person.origin].label} → ${ZONES[person.dest].label}` +
            ` via ${person.path.map((node) => (node === "hub" ? "hub" : node)).join("→")}` +
            (assigned === null ? " · waiting for a pod" : ` · pod ${assigned + 1}`)
        );
      } else if (person.podId === null && assigned !== null) {
        person.podId = assigned;
        events.push(`${person.name} redirected to pod ${assigned + 1} at ${ZONES[currentNode(person)].label}`);
      }
    }

    for (const pod of pods) {
      const { from, to } = podTarget(pod);
      const atStation = pod.progress < 0.45;
      if (!atStation) {
        continue;
      }

      for (const person of passengers) {
        if (person.status !== "riding" || person.podId !== pod.id) {
          continue;
        }
        const hop = nextHop(person);
        if (from !== hop && from !== person.dest) {
          continue;
        }
        if (from === hop) {
          person.pathIndex += 1;
        }
        pod.riders = pod.riders.filter((id) => id !== person.id);
        if (currentNode(person) === person.dest) {
          person.status = "done";
          person.podId = null;
          events.push(`${person.name} arrived at ${ZONES[person.dest].label}`);
        } else {
          person.status = "waiting";
          person.podId = pickPod(pods, currentNode(person), nextHop(person) as ZoneId);
          events.push(
            `${person.name} transferred at ${ZONES[from].label}` +
              (person.podId === null ? "" : ` → pod ${person.podId + 1}`)
          );
        }
      }

      for (const person of passengers) {
        if (person.status !== "waiting" || person.requestTick > t) {
          continue;
        }
        if (currentNode(person) !== from) {
          continue;
        }
        const hop = nextHop(person);
        if (!hop) {
          continue;
        }
        if (person.podId !== null && person.podId !== pod.id) {
          continue;
        }
        if (pod.riders.length >= pod.capacity) {
          continue;
        }
        if (to !== hop && !willVisitThen(pod, from, hop)) {
          continue;
        }
        person.status = "riding";
        person.podId = pod.id;
        pod.riders.push(person.id);
        events.push(`${person.name} boarded pod ${pod.id + 1} ${ZONES[from].label} → ${ZONES[hop].label}`);
      }
    }

    for (const pod of pods) {
      pod.progress += 0.2;
      while (pod.progress >= 1) {
        pod.progress -= 1;
        pod.routeIndex = (pod.routeIndex + 1) % pod.route.length;
      }
    }

    for (const person of passengers) {
      if (person.status === "waiting" && person.requestTick <= t) {
        person.wait += 1;
      }
      if (person.status === "riding") {
        person.travel += 1;
      }
    }

    snapshots.push({
      t,
      pods: pods.map((pod) => {
        const { from, to } = podTarget(pod);
        return {
          ...pod,
          riders: [...pod.riders],
          from,
          to,
          position: lerp(ZONES[from].position, ZONES[to].position, pod.progress),
        };
      }),
      waiting: passengers.filter((person) => person.status === "waiting" && person.requestTick <= t).map(clonePerson),
      riding: passengers.filter((person) => person.status === "riding").map(clonePerson),
      done: passengers.filter((person) => person.status === "done").map(clonePerson),
      events,
    });

    if (passengers.every((person) => person.status === "done") && t > 8) {
      break;
    }
  }

  return { snapshots, passengers: passengers.map(clonePerson) };
}

function clonePerson(person: MultiPassenger): MultiPassenger {
  return { ...person, path: [...person.path] };
}

export function summarizeMulti(passengers: MultiPassenger[]) {
  const done = passengers.filter((person) => person.status === "done");
  const waits = done.map((person) => person.wait);
  const travels = done.map((person) => person.travel);
  const totals = done.map((person) => person.wait + person.travel);
  const stats = (values: number[]) => {
    if (!values.length) {
      return { min: null, avg: null, max: null };
    }
    const sum = values.reduce((acc, value) => acc + value, 0);
    return {
      min: Math.min(...values),
      max: Math.max(...values),
      avg: Math.round((sum / values.length) * 10) / 10,
    };
  };
  return { count: done.length, wait: stats(waits), travel: stats(travels), total: stats(totals) };
}
