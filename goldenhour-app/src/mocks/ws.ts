/* ============================================================
   GoldenHour — Mock WebSocket Broadcast Simulator
   Simulates live updates when running in mock mode
   ============================================================ */
import type { WsMessage } from '../types/api';

type WsListener = (msg: WsMessage) => void;
const listeners = new Set<WsListener>();
let seq = 1;

export const mockWsBus = {
  subscribe(fn: WsListener) {
    listeners.add(fn);
    return () => listeners.delete(fn);
  },

  emit(event: string, data: unknown) {
    const msg: WsMessage = {
      event,
      seq: seq++,
      ts: new Date().toISOString(),
      data,
    };
    listeners.forEach((fn) => fn(msg));
  },
};

let simInterval: number | null = null;

export function startMockWsSimulation() {
  if (simInterval) return;

  // Emit periodic heartbeat and occasional driver movement / impact tick
  simInterval = window.setInterval(() => {
    // 1. Driver micro-movement
    mockWsBus.emit('driver.location', {
      driver_id: 'driver_rajesh',
      lat: 26.9085 + (Math.random() - 0.5) * 0.005,
      lng: 75.8012 + (Math.random() - 0.5) * 0.005,
      speed_kmh: 22 + Math.floor(Math.random() * 8),
      bearing: 145,
    });

    // 2. Platform impact counter tick
    if (Math.random() > 0.6) {
      mockWsBus.emit('impact.tick', {
        meals_rescued_delta: 1,
        co2e_kg_delta: 0.85,
      });
    }
  }, 4000);
}

export function stopMockWsSimulation() {
  if (simInterval) {
    clearInterval(simInterval);
    simInterval = null;
  }
}
