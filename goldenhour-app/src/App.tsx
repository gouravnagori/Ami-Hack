import React, { useEffect } from 'react';
import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { router } from './routes';
import { syncClockWithServer } from './lib/clock';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30, // 30s
      refetchOnWindowFocus: false,
    },
  },
});

export const App: React.FC = () => {
  useEffect(() => {
    // 1. Sync clock offset
    syncClockWithServer();

    // 2. Start mock WS updates ONLY when mocks are enabled
    if (import.meta.env.VITE_USE_MOCKS !== 'false') {
      import('./mocks/ws').then(({ startMockWsSimulation }) => {
        startMockWsSimulation();
      });
    }
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
};

export default App;

