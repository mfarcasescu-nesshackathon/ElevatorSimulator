"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Html, OrbitControls } from "@react-three/drei";
import type { Group } from "three";
import { CAR_COLORS, firstName } from "@/lib/events";
import type { TickSnapshot } from "@/lib/types";
import { PassengerGlyph } from "@/components/passenger-icon";

const FLOOR_HEIGHT = 1.2;
const SHAFT_SPACING = 2.6;

interface ElevatorSceneProps {
  snapshots: TickSnapshot[];
  playing: boolean;
  secondsPerTick: number;
  tick: number;
  onTick: (tick: number) => void;
}

export function ElevatorScene({
  snapshots,
  playing,
  secondsPerTick,
  tick,
  onTick,
}: ElevatorSceneProps) {
  const snapshot = snapshots[0];
  if (!snapshot) {
    return (
      <div className="flex h-full items-center justify-center px-8 text-center text-slate-400">
        Configure the building, then run the simulation to watch requests, assignments, and rides.
      </div>
    );
  }

  const numFloors = snapshot.num_floors;
  const numElevators = snapshot.num_elevators;
  const centerX = ((numElevators - 1) * SHAFT_SPACING) / 2;
  const centerY = (numFloors * FLOOR_HEIGHT) / 2;
  const cameraZ = Math.max(15, numFloors * 1.15, numElevators * 3.8);

  return (
    <Canvas
      camera={{ position: [centerX, centerY + 1.2, cameraZ], fov: 40 }}
      gl={{ antialias: true, alpha: false, preserveDrawingBuffer: true }}
    >
      <color attach="background" args={["#070b16"]} />
      <ambientLight intensity={0.8} />
      <directionalLight position={[8, 16, 12]} intensity={1.35} />
      <Building
        snapshots={snapshots}
        playing={playing}
        secondsPerTick={secondsPerTick}
        tick={tick}
        onTick={onTick}
      />
      <OrbitControls target={[centerX, centerY, 0]} enableDamping maxPolarAngle={Math.PI / 1.7} />
    </Canvas>
  );
}

function Building({ snapshots, playing, secondsPerTick, tick, onTick }: ElevatorSceneProps) {
  const snapshot = snapshots[0];
  const numFloors = snapshot.num_floors;
  const numElevators = snapshot.num_elevators;
  const width = numElevators * SHAFT_SPACING + 3.2;
  const height = numFloors * FLOOR_HEIGHT;
  const centerX = ((numElevators - 1) * SHAFT_SPACING) / 2;
  const cars = useRef<Array<Group | null>>([]);
  const tickRef = useRef(tick);
  const fracRef = useRef(0);

  tickRef.current = tick;

  useFrame((_, delta) => {
    let index = tickRef.current;
    if (playing && snapshots.length > 1 && index < snapshots.length - 1) {
      fracRef.current += delta / Math.max(secondsPerTick, 0.05);
      while (fracRef.current >= 1 && index < snapshots.length - 1) {
        fracRef.current -= 1;
        index += 1;
      }
      if (index !== tickRef.current) {
        tickRef.current = index;
        onTick(index);
      }
    }
    const next = Math.min(index + 1, snapshots.length - 1);
    const a = snapshots[index];
    const b = snapshots[next];
    const t = index === next ? 0 : fracRef.current;
    a.elevators.forEach((elevator, elevatorIndex) => {
      const group = cars.current[elevatorIndex];
      if (!group) {
        return;
      }
      const floorA = elevator.floor;
      const floorB = b.elevators[elevatorIndex]?.floor ?? floorA;
      group.position.y = (floorA + (floorB - floorA) * t - 1) * FLOOR_HEIGHT + 0.58;
    });
  });

  const floors = useMemo(
    () => Array.from({ length: numFloors }, (_, index) => index + 1),
    [numFloors]
  );
  const current = snapshots[Math.min(tick, snapshots.length - 1)] ?? snapshot;
  const firstSeen = useMemo(() => {
    const map = new Map<string, number>();
    snapshots.forEach((item, index) => {
      for (const person of item.waiting) {
        if (!map.has(person.id)) {
          map.set(person.id, index);
        }
      }
    });
    return map;
  }, [snapshots]);

  return (
    <group>
      <mesh position={[centerX, height / 2, -1.55]}>
        <boxGeometry args={[width, height + 0.8, 0.12]} />
        <meshStandardMaterial color="#1c2438" />
      </mesh>
      {floors.map((floor) => (
        <group key={floor}>
          <mesh position={[centerX, (floor - 1) * FLOOR_HEIGHT, 0.75]}>
            <boxGeometry args={[width, 0.07, 1.7]} />
            <meshStandardMaterial color="#4b5568" />
          </mesh>
          <HallPanel
            position={[-1.35, (floor - 1) * FLOOR_HEIGHT + 0.42, 0.35]}
            floor={floor}
            active={current.waiting.some((person) => person.floor === floor && person.is_new)}
          />
        </group>
      ))}
      {Array.from({ length: numElevators }, (_, elevatorId) => (
        <group key={`shaft-${elevatorId}`}>
          <mesh position={[elevatorId * SHAFT_SPACING, height / 2, 0]}>
            <boxGeometry args={[0.08, height, 0.08]} />
            <meshStandardMaterial color="#0f172a" />
          </mesh>
          <Html position={[elevatorId * SHAFT_SPACING, height + 0.35, 0]} center>
            <div
              className="rounded-md px-1.5 py-0.5 text-[10px] font-semibold text-slate-950"
              style={{ background: CAR_COLORS[elevatorId % CAR_COLORS.length] }}
            >
              E{elevatorId + 1}
            </div>
          </Html>
        </group>
      ))}
      {snapshot.elevators.map((elevator) => {
        const live = current.elevators[elevator.id] ?? elevator;
        return (
          <group
            key={elevator.id}
            ref={(node) => {
              cars.current[elevator.id] = node;
            }}
            position={[elevator.id * SHAFT_SPACING, 0.58, 0]}
          >
            <mesh>
              <boxGeometry args={[1.2, 1.1, 1.2]} />
              <meshStandardMaterial
                color={CAR_COLORS[elevator.id % CAR_COLORS.length]}
                metalness={0.2}
                roughness={0.32}
              />
            </mesh>
            {(live.onboard_people ?? []).slice(0, 4).map((rider, index) => (
              <Html
                key={rider.id}
                position={[-0.48 + (index % 2) * 0.48, 0.15, 0.72 + Math.floor(index / 2) * 0.28]}
                center
              >
                <PassengerGlyph
                  icon={rider.icon}
                  role={rider.role}
                  name={firstName(rider.name)}
                  dest={rider.dest}
                  size="sm"
                />
              </Html>
            ))}
            <Html position={[0, 1.05, 0.7]} center>
              <div className="min-w-[54px] rounded-full bg-slate-950/85 px-2 py-1 text-center text-[11px] font-semibold text-white shadow">
                {live.load}/{live.capacity}
                <span className="ml-1 text-[10px] font-normal text-amber-200">pax</span>
              </div>
            </Html>
          </group>
        );
      })}
      {current.waiting.map((person) => {
        const seen = firstSeen.get(person.id) ?? tick;
        const walk = Math.min(1, (tick - seen) / 2);
        const kioskX = -1.15;
        const doorX = (person.elevator ?? 0) * SHAFT_SPACING + 0.95;
        const x = kioskX + (doorX - kioskX) * walk;
        return (
          <group key={person.id} position={[x, (person.floor - 1) * FLOOR_HEIGHT + 0.22, 0.9]}>
            <Html center>
              <PassengerGlyph
                icon={person.icon}
                role={person.role}
                name={firstName(person.name)}
                dest={person.dest}
              />
            </Html>
          </group>
        );
      })}
    </group>
  );
}

function HallPanel({
  position,
  floor,
  active,
}: {
  position: [number, number, number];
  floor: number;
  active: boolean;
}) {
  return (
    <group position={position}>
      <mesh>
        <boxGeometry args={[0.22, 0.38, 0.08]} />
        <meshStandardMaterial color={active ? "#fbbf24" : "#334155"} emissive={active ? "#f59e0b" : "#000"} emissiveIntensity={active ? 0.6 : 0} />
      </mesh>
      <Html position={[0, 0.32, 0.1]} center>
        <div className={`text-[9px] ${active ? "text-amber-300" : "text-slate-500"}`}>F{floor}</div>
      </Html>
    </group>
  );
}
