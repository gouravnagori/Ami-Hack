/* useLive — WebSocket connection hook with TanStack Query cache updates */
import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { liveSocket } from '../lib/ws';
import { useSessionStore } from '../store/session';
import type { WsMessage } from '../types/api';

export function useLive() {
  const queryClient = useQueryClient();
  const isAuth = useSessionStore((s) => s.isAuthenticated);
  const connectedRef = useRef(false);

  const handleMessage = useCallback(
    (msg: WsMessage) => {
      switch (msg.event) {
        case 'donation.updated':
          queryClient.invalidateQueries({ queryKey: ['donations'] });
          queryClient.invalidateQueries({ queryKey: ['donation', (msg.data as { id: string }).id] });
          break;
        case 'allocation.updated':
          queryClient.invalidateQueries({ queryKey: ['donations'] });
          queryClient.invalidateQueries({ queryKey: ['incoming'] });
          break;
        case 'offer.created':
        case 'offer.expired':
        case 'offer.withdrawn':
          queryClient.invalidateQueries({ queryKey: ['offers'] });
          break;
        case 'capacity.updated':
          queryClient.invalidateQueries({ queryKey: ['capacity'] });
          break;
        case 'route.updated':
          queryClient.invalidateQueries({ queryKey: ['route'] });
          break;
        case 'driver.location':
          // update driver location in cache for maps
          queryClient.setQueryData(['driver-location', (msg.data as { driver_id: string }).driver_id], msg.data);
          break;
        case 'impact.tick':
          queryClient.invalidateQueries({ queryKey: ['impact'] });
          break;
        case 'alert.risk':
        case 'sim.log':
          queryClient.invalidateQueries({ queryKey: ['admin-live'] });
          queryClient.invalidateQueries({ queryKey: ['admin-metrics'] });
          break;
      }
    },
    [queryClient]
  );

  useEffect(() => {
    if (isAuth && !connectedRef.current) {
      liveSocket.connect();
      connectedRef.current = true;
    } else if (!isAuth && connectedRef.current) {
      liveSocket.disconnect();
      connectedRef.current = false;
    }
  }, [isAuth]);

  useEffect(() => {
    const unsub = liveSocket.subscribe(handleMessage);
    return unsub;
  }, [handleMessage]);

  return { connected: liveSocket.connected };
}
