import type { SimConfig, SimulationResponse } from "./types";

export async function runSimulation(config: SimConfig): Promise<SimulationResponse> {
  const response = await fetch("/api/simulate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Simulation failed");
  }
  return payload as SimulationResponse;
}
