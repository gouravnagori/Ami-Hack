/* ============================================================
   GoldenHour — Clock (server-time offset)
   ============================================================ */
import { api } from './api';

let offsetMs = 0;

export async function syncClock(): Promise<void> {
  try {
    const before = Date.now();
    const data = await api.get<{ time?: string; server_time?: string }>('/time');
    const after = Date.now();
    const rawTime = data.server_time || data.time;
    if (rawTime) {
      const serverTime = new Date(rawTime).getTime();
      const rtt = after - before;
      offsetMs = serverTime - before - rtt / 2;
    }
  } catch {
    // silently fail — use local clock
    offsetMs = 0;
  }
}

export const syncClockWithServer = syncClock;

export function getServerNow(): Date {
  return new Date(Date.now() + offsetMs);
}

export function getOffsetMs(): number {
  return offsetMs;
}
