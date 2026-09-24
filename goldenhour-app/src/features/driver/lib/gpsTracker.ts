/* ============================================================
   GoldenHour — Driver GPS Telemetry Tracker
   Throttles GPS updates to avoid draining battery
   ============================================================ */
import { api } from '../../../lib/api';

let watchId: number | null = null;
let lastPingTime = 0;
const MIN_PING_INTERVAL_MS = 6000; // 6s throttle

export const gpsTracker = {
  startTracking(driverId: string) {
    if (!navigator.geolocation || watchId !== null) return;

    watchId = navigator.geolocation.watchPosition(
      (pos) => {
        const now = Date.now();
        if (now - lastPingTime < MIN_PING_INTERVAL_MS) return;
        lastPingTime = now;

        api
          .post('/api/driver/location', {
            driver_id: driverId,
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
            speed: pos.coords.speed || 0,
            heading: pos.coords.heading || 0,
          })
          .catch(() => {
            // Location ping failure is non-blocking
          });
      },
      (err) => {
        console.warn('GPS position watch warning:', err.message);
      },
      {
        enableHighAccuracy: true,
        maximumAge: 5000,
        timeout: 10000,
      }
    );
  },

  stopTracking() {
    if (watchId !== null) {
      navigator.geolocation.clearWatch(watchId);
      watchId = null;
    }
  },
};
