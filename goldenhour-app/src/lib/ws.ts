/* ============================================================
   GoldenHour — WebSocket Client
   Reconnecting socket with seq replay, exponential backoff
   ============================================================ */
import type { WsMessage } from '../types/api';
import { useSessionStore } from '../store/session';

type WsHandler = (msg: WsMessage) => void;

const WS_URL = import.meta.env.VITE_WS_URL || `ws://${window.location.host}/api/v1/ws`;
const MAX_BACKOFF = 30_000;
const INITIAL_BACKOFF = 1_000;

class LiveSocket {
  private ws: WebSocket | null = null;
  private handlers = new Set<WsHandler>();
  private lastSeq = 0;
  private backoff = INITIAL_BACKOFF;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private intentionalClose = false;
  private _connected = false;

  get connected() { return this._connected; }

  connect() {
    this.intentionalClose = false;
    this.createConnection();
  }

  private createConnection() {
    const token = useSessionStore.getState().accessToken;
    if (!token) return;

    const url = `${WS_URL}?token=${token}${this.lastSeq ? `&last_seq=${this.lastSeq}` : ''}`;

    try {
      this.ws = new WebSocket(url);
    } catch {
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this._connected = true;
      this.backoff = INITIAL_BACKOFF;
    };

    this.ws.onmessage = (e) => {
      try {
        const msg: WsMessage = JSON.parse(e.data);
        if (msg.seq) this.lastSeq = msg.seq;
        this.handlers.forEach(h => h(msg));
      } catch {
        // ignore malformed messages
      }
    };

    this.ws.onclose = () => {
      this._connected = false;
      if (!this.intentionalClose) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.backoff = Math.min(this.backoff * 2, MAX_BACKOFF);
      this.createConnection();
    }, this.backoff);
  }

  disconnect() {
    this.intentionalClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
    this._connected = false;
  }

  subscribe(handler: WsHandler) {
    this.handlers.add(handler);
    return () => { this.handlers.delete(handler); };
  }

  send(data: unknown) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  sendLocation(lat: number, lng: number, speed: number, heading: number) {
    this.send({
      event: 'driver.location',
      data: { lat, lng, speed, heading, ts: new Date().toISOString() },
    });
  }
}

export const liveSocket = new LiveSocket();
