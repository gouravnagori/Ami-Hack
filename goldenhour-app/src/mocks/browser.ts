/* ============================================================
   GoldenHour — MSW Browser Setup
   ============================================================ */
import { setupWorker } from 'msw/browser';
import { handlers } from './handlers';

export const worker = setupWorker(...handlers);

export async function enableMocking() {
  // If user sets VITE_USE_MOCKS === 'false', bypass MSW and connect to backend
  if (import.meta.env.VITE_USE_MOCKS === 'false') {
    return;
  }

  // Start the service worker in browser
  try {
    await worker.start({
      onUnhandledRequest: 'bypass',
      serviceWorker: {
        url: '/mockServiceWorker.js',
      },
    });
  } catch (err) {
    console.warn('MSW worker registration fallback:', err);
  }
}
