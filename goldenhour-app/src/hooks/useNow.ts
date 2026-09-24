/* useNow — shared server-corrected Date ticking each second */
import { useState, useEffect } from 'react';
import { getServerNow } from '../lib/clock';

let globalNow = getServerNow();
const listeners = new Set<(d: Date) => void>();
let interval: ReturnType<typeof setInterval> | null = null;

function startTicker() {
  if (interval) return;
  interval = setInterval(() => {
    globalNow = getServerNow();
    listeners.forEach((fn) => fn(globalNow));
  }, 1000);
}

export function useNow(): Date {
  const [now, setNow] = useState(globalNow);

  useEffect(() => {
    listeners.add(setNow);
    startTicker();
    return () => {
      listeners.delete(setNow);
      if (listeners.size === 0 && interval) {
        clearInterval(interval);
        interval = null;
      }
    };
  }, []);

  return now;
}

/** Get remaining seconds until a deadline */
export function useRemainingSeconds(deadline: string | Date): number {
  const now = useNow();
  const target = typeof deadline === 'string' ? new Date(deadline) : deadline;
  return Math.max(0, Math.floor((target.getTime() - now.getTime()) / 1000));
}
