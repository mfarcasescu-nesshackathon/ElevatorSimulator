import type { OnboardPerson, TickSnapshot, TimelineEvent, WaitingPassenger } from "./types";

export const CAR_COLORS = [
  "#2f8cff",
  "#ff5a3d",
  "#3dcc6b",
  "#f5c542",
  "#c75cff",
  "#3ee0e8",
  "#ff8a2b",
  "#9aa0a6",
  "#ff7ab6",
  "#6b8f3f",
];

export function elevatorLabel(id: number | null): string {
  if (id === null || id === undefined) {
    return "an elevator";
  }
  return `Elevator ${id + 1}`;
}

export function firstName(name: string): string {
  return name.split(" ")[0] || name;
}

function identity(person: WaitingPassenger | OnboardPerson | undefined, fallbackId: string) {
  return {
    name: person?.name || fallbackId,
    role: person?.role === "employee" ? "employee" : "guest",
    icon: person?.icon || "user",
  } as const;
}

export function collectEvents(
  snapshots: TickSnapshot[],
  tick: number,
  limit = 8
): TimelineEvent[] {
  if (!snapshots.length) {
    return [];
  }
  const events: TimelineEvent[] = [];
  for (let index = 0; index <= tick; index += 1) {
    const current = snapshots[index];
    const previous = index > 0 ? snapshots[index - 1] : undefined;
    const prevWaiting = new Set(previous?.waiting.map((person) => person.id) ?? []);
    const prevOnboard = new Set(previous?.elevators.flatMap((car) => car.onboard) ?? []);
    const currOnboard = new Set(current.elevators.flatMap((car) => car.onboard));
    const prevPeople = new Map(
      previous?.elevators.flatMap((car) => car.onboard_people ?? []).map((person) => [person.id, person]) ?? []
    );

    for (const person of current.waiting) {
      if (!prevWaiting.has(person.id)) {
        const who = identity(person, person.id);
        events.push({
          key: `${index}-req-${person.id}`,
          tick: index,
          kind: "request",
          text: `${who.name} (${who.role}) requested floor ${person.floor} → ${person.dest}`,
          elevator: person.elevator,
          source: person.floor,
          dest: person.dest,
          ...who,
        });
        events.push({
          key: `${index}-asg-${person.id}`,
          tick: index,
          kind: "assign",
          text: `${who.name} directed to ${elevatorLabel(person.elevator)}`,
          elevator: person.elevator,
          dest: person.dest,
          ...who,
        });
      }
    }

    for (const car of current.elevators) {
      for (const rider of car.onboard_people ?? []) {
        if (!prevOnboard.has(rider.id)) {
          const who = identity(rider, rider.id);
          events.push({
            key: `${index}-brd-${rider.id}`,
            tick: index,
            kind: "board",
            text: `${who.name} boarded ${elevatorLabel(car.id)} toward floor ${rider.dest} (${car.load}/${car.capacity})`,
            elevator: car.id,
            dest: rider.dest,
            ...who,
          });
        }
      }
    }

    if (previous) {
      for (const passengerId of prevOnboard) {
        if (!currOnboard.has(passengerId) && !current.waiting.some((person) => person.id === passengerId)) {
          const rider = prevPeople.get(passengerId);
          const who = identity(rider, passengerId);
          events.push({
            key: `${index}-out-${passengerId}`,
            tick: index,
            kind: "alight",
            text: `${who.name} arrived at floor ${rider?.dest ?? "?"} and stepped off`,
            elevator: previous.elevators.find((car) => car.onboard.includes(passengerId))?.id ?? null,
            dest: rider?.dest,
            ...who,
          });
        }
      }
    }
  }
  return limit > 0 ? events.slice(-limit) : events;
}
