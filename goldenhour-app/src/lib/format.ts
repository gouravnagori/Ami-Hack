/* ============================================================
   GoldenHour — Format Utilities
   ============================================================ */
import { formatDistanceToNow, format } from 'date-fns';

/** Format seconds as "mm:ss" or "h:mm" if above one hour */
export function formatCountdown(seconds: number): string {
  if (seconds <= 0) return '0:00';
  if (seconds >= 3600) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}:${String(m).padStart(2, '0')}`;
  }
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}

/** "3m 40s" style */
export function formatDurationShort(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return s > 0 ? `${m}m ${s}s` : `${m}m`;
}

/** "2.1 km" */
export function formatDistance(metres: number): string {
  if (metres < 1000) return `${Math.round(metres)} m`;
  return `${(metres / 1000).toFixed(1)} km`;
}

/** "214 portions" */
export function formatPortions(n: number): string {
  return `${n} portion${n !== 1 ? 's' : ''}`;
}

/** "38 min to spare" */
export function formatSlack(seconds: number): string {
  if (seconds <= 0) return 'No time to spare';
  const m = Math.round(seconds / 60);
  return `${m} min to spare`;
}

/** Relative time like "3 minutes ago" */
export function formatRelative(iso: string): string {
  return formatDistanceToNow(new Date(iso), { addSuffix: true });
}

/** "9:42 pm" */
export function formatTime(iso: string): string {
  return format(new Date(iso), 'h:mm a').toLowerCase();
}

/** "Mon, Sep 22" */
export function formatDate(iso: string): string {
  return format(new Date(iso), 'EEE, MMM d');
}

/** Format weight */
export function formatWeight(kg: number): string {
  if (kg < 1) return `${Math.round(kg * 1000)} g`;
  return `${kg.toFixed(1)} kg`;
}

/** CO2e avoided */
export function formatCO2(kg: number): string {
  if (kg >= 1000) return `${(kg / 1000).toFixed(1)} t`;
  return `${kg.toFixed(1)} kg`;
}
