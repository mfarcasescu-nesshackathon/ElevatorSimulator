export interface WaitingPassenger {
  id: string;
  floor: number;
  dest: number;
  elevator: number | null;
  request_time: number;
  is_new: boolean;
  name: string;
  role: "employee" | "guest";
  icon: string;
}

export interface OnboardPerson {
  id: string;
  dest: number;
  name: string;
  role: "employee" | "guest";
  icon: string;
}

export interface ElevatorState {
  id: number;
  floor: number;
  direction: number;
  load: number;
  capacity: number;
  onboard: string[];
  onboard_dests: number[];
  onboard_people: OnboardPerson[];
}

export interface TickSnapshot {
  t: number;
  done: boolean;
  num_floors: number;
  num_elevators: number;
  capacity: number;
  elevators: ElevatorState[];
  waiting: WaitingPassenger[];
}

export interface SimulationResponse {
  scheduler: string;
  config: {
    num_elevators: number;
    num_floors: number;
    capacity: number;
  };
  ticks: number;
  positions: number[][];
  snapshots: TickSnapshot[];
  stats: {
    count: number;
    wait: { min: number | null; max: number | null; avg: number | null };
    total: { min: number | null; max: number | null; avg: number | null };
    travel: { min: number | null; max: number | null; avg: number | null };
  };
  observations: string[];
  request_count: number;
  passengers: Array<{
    id: string;
    name: string;
    role: "employee" | "guest";
    icon: string;
    source: number;
    dest: number;
    request_time: number;
    assigned_elevator: number | null;
    wait_time: number | null;
    travel_time: number | null;
    total_time: number | null;
  }>;
}

export interface SimConfig {
  elevators: number;
  floors: number;
  capacity: number;
  passengers: number;
  scheduler: string;
  seed: number;
}

export interface TimelineEvent {
  key: string;
  tick: number;
  kind: "request" | "assign" | "board" | "alight";
  text: string;
  elevator: number | null;
  name: string;
  role: "employee" | "guest";
  icon: string;
  source?: number;
  dest?: number;
}
