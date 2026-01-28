/**
 * NovAIC Gateway WebSocket Client
 * 
 * Provides real-time bidirectional communication for chat and events.
 * Replaces Tauri Events with WebSocket messages.
 */

const GATEWAY_WS = import.meta.env.VITE_GATEWAY_WS || 'ws://127.0.0.1:9000/ws';

export interface WSEvent {
  type: string;
  data: unknown;
  timestamp: string;
}

export type EventCallback = (data: unknown) => void;

/**
 * Gateway WebSocket client
 */
class GatewayWebSocket {
  private ws: WebSocket | null = null;
  private clientId: string;
  private listeners: Map<string, Set<EventCallback>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000;
  private connected = false;
  private connecting = false;

  constructor() {
    this.clientId = crypto.randomUUID();
  }

  /**
   * Connect to the Gateway WebSocket
   */
  async connect(): Promise<void> {
    if (this.connected || this.connecting) {
      return;
    }

    this.connecting = true;

    return new Promise((resolve, reject) => {
      try {
        const url = `${GATEWAY_WS}/${this.clientId}`;
        console.log(`[WS] Connecting to ${url}...`);
        
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          console.log('[WS] Connected');
          this.connected = true;
          this.connecting = false;
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onerror = (error) => {
          console.error('[WS] Error:', error);
          this.connecting = false;
          reject(error);
        };

        this.ws.onclose = (event) => {
          console.log(`[WS] Disconnected: ${event.code} ${event.reason}`);
          this.connected = false;
          this.connecting = false;
          this.handleDisconnect();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data) as WSEvent;
            this.handleMessage(data);
          } catch (e) {
            console.error('[WS] Failed to parse message:', e);
          }
        };
      } catch (error) {
        this.connecting = false;
        reject(error);
      }
    });
  }

  /**
   * Handle incoming WebSocket message
   */
  private handleMessage(event: WSEvent) {
    const listeners = this.listeners.get(event.type);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(event.data);
        } catch (e) {
          console.error(`[WS] Listener error for ${event.type}:`, e);
        }
      });
    }

    // Also notify 'all' listeners
    const allListeners = this.listeners.get('*');
    if (allListeners) {
      allListeners.forEach(callback => {
        try {
          callback(event);
        } catch (e) {
          console.error('[WS] All-listener error:', e);
        }
      });
    }
  }

  /**
   * Handle disconnection with auto-reconnect
   */
  private handleDisconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * this.reconnectAttempts;
      console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect().catch(e => {
          console.error('[WS] Reconnect failed:', e);
        });
      }, delay);
    } else {
      console.error('[WS] Max reconnect attempts reached');
      // Notify listeners about connection loss
      const listeners = this.listeners.get('disconnect');
      if (listeners) {
        listeners.forEach(callback => callback(null));
      }
    }
  }

  /**
   * Subscribe to an event type
   */
  on(type: string, callback: EventCallback): () => void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }
    this.listeners.get(type)!.add(callback);

    // Return unsubscribe function
    return () => {
      const listeners = this.listeners.get(type);
      if (listeners) {
        listeners.delete(callback);
      }
    };
  }

  /**
   * Unsubscribe from an event type
   */
  off(type: string, callback?: EventCallback) {
    if (callback) {
      const listeners = this.listeners.get(type);
      if (listeners) {
        listeners.delete(callback);
      }
    } else {
      this.listeners.delete(type);
    }
  }

  /**
   * Send a chat message
   */
  sendChat(message: string, options?: {
    model?: string;
    mode?: 'agent' | 'chat';
    apiKeyId?: string;
  }) {
    this.send({
      type: 'chat',
      message,
      model: options?.model,
      mode: options?.mode || 'agent',
      api_key_id: options?.apiKeyId,
    });
  }

  /**
   * Send interrupt signal
   */
  sendInterrupt() {
    this.send({ type: 'interrupt' });
  }

  /**
   * Send clear history signal
   */
  sendClear() {
    this.send({ type: 'clear' });
  }

  /**
   * Send ping to check connection
   */
  sendPing() {
    this.send({ type: 'ping' });
  }

  /**
   * Send a message to the server
   */
  private send(data: object) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('[WS] Cannot send: not connected');
      return;
    }
    this.ws.send(JSON.stringify(data));
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connected && this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Disconnect from the server
   */
  disconnect() {
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent auto-reconnect
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connected = false;
    this.listeners.clear();
  }

  /**
   * Get client ID
   */
  getClientId(): string {
    return this.clientId;
  }
}

// Export singleton instance
export const gateway = new GatewayWebSocket();

export default gateway;
