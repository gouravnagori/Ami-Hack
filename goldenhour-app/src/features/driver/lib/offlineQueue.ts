/* ============================================================
   GoldenHour — Driver Offline Stop Queue
   Ensures stop completions survive patchy connectivity
   ============================================================ */
import { api } from '../../../lib/api';

interface QueuedAction {
  id: string;
  routeId: string;
  stopId: string;
  otp?: string;
  timestamp: number;
}

const STORAGE_KEY = 'goldenhour_driver_offline_queue';

export const offlineQueue = {
  getQueue(): QueuedAction[] {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  },

  enqueue(routeId: string, stopId: string, otp?: string) {
    const queue = this.getQueue();
    queue.push({
      id: `${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      routeId,
      stopId,
      otp,
      timestamp: Date.now(),
    });
    localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
  },

  async flush(): Promise<number> {
    const queue = this.getQueue();
    if (queue.length === 0) return 0;

    let synced = 0;
    const remaining: QueuedAction[] = [];

    for (const action of queue) {
      try {
        await api.post(`/api/routes/${action.routeId}/stops/${action.stopId}/done`, {
          otp: action.otp,
        });
        synced++;
      } catch {
        remaining.push(action);
      }
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(remaining));
    return synced;
  },
};
