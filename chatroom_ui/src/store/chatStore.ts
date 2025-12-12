import { create } from 'zustand';
import type { Message, ThoughtStep, ToolCall } from '../hooks/useChat';

/**
 * 聊天状态接口
 */
interface ChatState {
  messages: Message[];
  thoughts: ThoughtStep[];
  toolCalls: ToolCall[];
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  addMessage: (message: Message) => void;
  addThought: (thought: ThoughtStep) => void;
  updateThought: (id: string, updates: Partial<ThoughtStep>) => void;
  addToolCall: (toolCall: ToolCall) => void;
  updateToolCall: (id: string, updates: Partial<ToolCall>) => void;
  setConnected: (connected: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearMessages: () => void;
}

/**
 * 聊天状态Store (使用Zustand)
 */
export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  thoughts: [],
  toolCalls: [],
  isConnected: false,
  isLoading: false,
  error: null,
  
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),
  
  addThought: (thought) =>
    set((state) => ({
      thoughts: [...state.thoughts, thought],
    })),
  
  updateThought: (id, updates) =>
    set((state) => ({
      thoughts: state.thoughts.map((t) =>
        t.id === id ? { ...t, ...updates } : t
      ),
    })),
  
  addToolCall: (toolCall) =>
    set((state) => ({
      toolCalls: [...state.toolCalls, toolCall],
    })),
  
  updateToolCall: (id, updates) =>
    set((state) => ({
      toolCalls: state.toolCalls.map((tc) =>
        tc.id === id ? { ...tc, ...updates } : tc
      ),
    })),
  
  setConnected: (connected) =>
    set({ isConnected: connected }),
  
  setLoading: (loading) =>
    set({ isLoading: loading }),
  
  setError: (error) =>
    set({ error }),
  
  clearMessages: () =>
    set({
      messages: [],
      thoughts: [],
      toolCalls: [],
      error: null,
    }),
}));
