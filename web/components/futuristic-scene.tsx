"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Html, OrbitControls } from "@react-three/drei";
import { Quaternion, Vector3, type Group } from "three";
import { POD_COLORS, ZONES, type MultiSnapshot, type ZoneId } from "@/lib/multi-sim";

export function FuturisticScene({
  snapshots,
  playing,
  secondsPerTick,
  tick,
  onTick,
}: {
  snapshots: MultiSnapshot[];
  playing: boolean;
  secondsPerTick: number;
  tick: number;
  onTick: (tick: number) => void;
}) {
  if (!snapshots.length) {
    return (
      <div className="flex h-full items-center justify-center px-8 text-center text-slate-400">
        Run the MULTI network to watch pods move vertically, horizontally, and through the rotating exchange.
      </div>
    );
  }

  return (
    <Canvas camera={{ position: [16, 8, 18], fov: 40 }} gl={{ antialias: true, alpha: false, preserveDrawingBuffer: true }}>
      <color attach="background" args={["#070b16"]} />
      <ambientLight intensity={0.75} />
      <directionalLight position={[10, 18, 12]} intensity={1.4} />
      <pointLight position={[0, 2, 0]} intensity={1.2} color="#f59e0b" />
      <Network snapshots={snapshots} playing={playing} secondsPerTick={secondsPerTick} tick={tick} onTick={onTick} />
      <OrbitControls target={[0, 0, 0]} enableDamping maxPolarAngle={Math.PI / 1.55} />
    </Canvas>
  );
}

function Network({
  snapshots,
  playing,
  secondsPerTick,
  tick,
  onTick,
}: {
  snapshots: MultiSnapshot[];
  playing: boolean;
  secondsPerTick: number;
  tick: number;
  onTick: (tick: number) => void;
}) {
  const tickRef = useRef(tick);
  const fracRef = useRef(0);
  const podsRef = useRef<Array<Group | null>>([]);
  tickRef.current = tick;
  const current = snapshots[Math.min(tick, snapshots.length - 1)];

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
    a.pods.forEach((pod, podIndex) => {
      const group = podsRef.current[podIndex];
      if (!group) {
        return;
      }
      const other = b.pods[podIndex] ?? pod;
      group.position.set(
        pod.position.x + (other.position.x - pod.position.x) * t,
        pod.position.y + (other.position.y - pod.position.y) * t,
        pod.position.z + (other.position.z - pod.position.z) * t
      );
    });
  });

  return (
    <group>
      <DiamondShell />
      <Shaft from="lobby" to="hub" color="#fbbf24" />
      <Shaft from="hub" to="B" color="#38bdf8" />
      <Shaft from="hub" to="C" color="#34d399" />
      <Shaft from="hub" to="D" color="#c084fc" />
      <Shaft from="hub" to="E" color="#fb7185" />
      <HubRing />
      {(Object.keys(ZONES) as ZoneId[]).map((id) => (
        <ZoneMarker key={id} id={id} waiting={current.waiting.filter((person) => person.origin === id).length} />
      ))}
      {current.pods.map((pod) => (
        <group
          key={pod.id}
          ref={(node) => {
            podsRef.current[pod.id] = node;
          }}
          position={[pod.position.x, pod.position.y, pod.position.z]}
        >
          <mesh>
            <boxGeometry args={[1.15, 0.85, 1.15]} />
            <meshStandardMaterial
              color={POD_COLORS[pod.id % POD_COLORS.length]}
              metalness={0.45}
              roughness={0.22}
              emissive={POD_COLORS[pod.id % POD_COLORS.length]}
              emissiveIntensity={0.18}
            />
          </mesh>
          <Html position={[0, 0.85, 0]} center>
            <div className="rounded-full bg-slate-950/85 px-2 py-0.5 text-[10px] font-semibold text-white">
              Pod {pod.id + 1} · {pod.riders.length}/{pod.capacity}
            </div>
          </Html>
        </group>
      ))}
    </group>
  );
}

function DiamondShell() {
  return (
    <group>
      <mesh position={[0, 0.4, 0]} rotation={[0, Math.PI / 4, 0]}>
        <octahedronGeometry args={[7.4, 0]} />
        <meshStandardMaterial color="#122033" transparent opacity={0.22} metalness={0.3} roughness={0.15} />
      </mesh>
      <mesh position={[0, -8.2, 0]}>
        <cylinderGeometry args={[1.15, 1.6, 6.4, 8]} />
        <meshStandardMaterial color="#1e293b" transparent opacity={0.55} />
      </mesh>
    </group>
  );
}

function Shaft({ from, to, color }: { from: ZoneId; to: ZoneId; color: string }) {
  const { mid, quat, length } = useMemo(() => {
    const a = ZONES[from].position;
    const b = ZONES[to].position;
    const start = new Vector3(a.x, a.y, a.z);
    const end = new Vector3(b.x, b.y, b.z);
    const dir = end.clone().sub(start);
    const length = dir.length() || 1;
    const mid = start.clone().add(end).multiplyScalar(0.5);
    const quat = new Quaternion().setFromUnitVectors(new Vector3(0, 1, 0), dir.normalize());
    return { mid, quat, length };
  }, [from, to]);

  return (
    <mesh position={mid} quaternion={quat}>
      <cylinderGeometry args={[0.12, 0.12, length, 10]} />
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.35} />
    </mesh>
  );
}

function HubRing() {
  const ref = useRef<Group>(null);
  useFrame((_, delta) => {
    if (ref.current) {
      ref.current.rotation.y += delta * 0.6;
    }
  });
  return (
    <group ref={ref}>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.7, 0.08, 8, 32]} />
        <meshStandardMaterial color="#f59e0b" emissive="#f59e0b" emissiveIntensity={0.5} />
      </mesh>
      <mesh>
        <sphereGeometry args={[0.45, 16, 16]} />
        <meshStandardMaterial color="#fbbf24" emissive="#f59e0b" emissiveIntensity={0.4} />
      </mesh>
    </group>
  );
}

function ZoneMarker({ id, waiting }: { id: ZoneId; waiting: number }) {
  const zone = ZONES[id];
  return (
    <group position={[zone.position.x, zone.position.y, zone.position.z]}>
      <mesh>
        <octahedronGeometry args={[id === "hub" ? 0.2 : 0.55, 0]} />
        <meshStandardMaterial color={zone.color} emissive={zone.color} emissiveIntensity={0.3} />
      </mesh>
      <Html position={[0, id === "lobby" ? -1.1 : 0.95, 0]} center>
        <div className="rounded-md bg-slate-950/80 px-2 py-1 text-center text-[10px] text-white">
          <div className="font-semibold">{zone.label}</div>
          {waiting > 0 ? <div className="text-amber-300">{waiting} waiting</div> : null}
        </div>
      </Html>
    </group>
  );
}
