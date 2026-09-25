import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import './lib/i18n';
import App from './App';

async function boot() {
  // Only load and start MSW when explicitly in mock mode
  if (import.meta.env.VITE_USE_MOCKS !== 'false') {
    const { enableMocking } = await import('./mocks/browser');
    await enableMocking();
  }

  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>
  );
}

boot();
