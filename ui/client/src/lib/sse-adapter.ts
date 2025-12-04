import { v4 as uuidv4 } from 'uuid';

export type SSEEventType = 'thought' | 'tool' | 'system' | 'message' | 'error' | 'done';

export interface SSEEventData {
  id: string;
  timestamp: string;
  type: SSEEventType;
  [key: string]: any;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  metadata?: Record<string, any>;
}

export class SSEClient {
  private eventSource: EventSource | null = null;
  private listeners: Record<string, ((data: SSEEventData) => void)[]> = {};
  private baseUrl: string;

  constructor(baseUrl: string = '/api/v1/chat/stream') {
    this.baseUrl = baseUrl;
  }

  public connect(message: string, threadId?: string, clientId?: string) {
    if (this.eventSource) {
      this.eventSource.close();
    }

    const url = new URL(this.baseUrl, window.location.origin);
    url.searchParams.append('message', message);
    if (threadId) url.searchParams.append('thread_id', threadId);
    if (clientId) url.searchParams.append('client_id', clientId);

    this.eventSource = new EventSource(url.toString());

    // Setup default listeners
    this.eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.emit('message', data);
      } catch (e) {
        console.error('Error parsing SSE message:', e);
      }
    };

    // Setup custom event listeners
    const eventTypes: SSEEventType[] = ['thought', 'tool', 'system', 'error', 'done'];
    eventTypes.forEach(type => {
      this.eventSource?.addEventListener(type, (event) => {
        try {
          const data = JSON.parse(event.data);
          this.emit(type, data);
        } catch (e) {
          console.error(`Error parsing SSE ${type} event:`, e);
        }
      });
    });

    this.eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      this.emit('error', { 
        id: uuidv4(), 
        timestamp: new Date().toISOString(), 
        type: 'error', 
        error: 'Connection error' 
      });
      this.close();
    };
  }

  public on(type: string, callback: (data: SSEEventData) => void) {
    if (!this.listeners[type]) {
      this.listeners[type] = [];
    }
    this.listeners[type].push(callback);
    return () => this.off(type, callback);
  }

  public off(type: string, callback: (data: SSEEventData) => void) {
    if (!this.listeners[type]) return;
    this.listeners[type] = this.listeners[type].filter(cb => cb !== callback);
  }

  private emit(type: string, data: SSEEventData) {
    if (this.listeners[type]) {
      this.listeners[type].forEach(cb => cb(data));
    }
  }

  public close() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}
