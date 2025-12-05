import { create } from 'zustand';

/**
 * 消息类型定义
 */
export interface Message {
  id: string;
  timestamp: string;
  type: 'message' | 'thought' | 'tool' | 'system';
  role?: 'user' | 'assistant';
  source?: string; // user/api/admin/livestream/fleet
  content: string;
  metadata?: Record<string, any>;
  // Generative UI相关
  component?: string; // 组件名称
  componentProps?: Record<string, any>; // 组件props
}

/**
 * 思维链步骤
 */
export interface ThoughtStep {
  id: string;
  timestamp: string;
  content: string;
  status: 'thinking' | 'completed';
}

/**
 * 工具调用
 */
export interface ToolCall {
  id: string;
  timestamp: string;
  tool_name: string;
  status: 'calling' | 'success' | 'error';
  input?: Record<string, any>;
  output?: any;
  error?: string;
}

/**
 * 聊天状态
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
  addToolCall: (toolCall: ToolCall) => void;
  updateToolCall: (id: string, updates: Partial<ToolCall>) => void;
  setConnected: (connected: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearMessages: () => void;
}

/**
 * Zustand Store
 */
export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  thoughts: [],
  toolCalls: [],
  isConnected: false,
  isLoading: false,
  error: null,
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message],
  })),
  
  addThought: (thought) => set((state) => ({
    thoughts: [...state.thoughts, thought],
  })),
  
  addToolCall: (toolCall) => set((state) => ({
    toolCalls: [...state.toolCalls, toolCall],
  })),
  
  updateToolCall: (id, updates) => set((state) => ({
    toolCalls: state.toolCalls.map((tc) =>
      tc.id === id ? { ...tc, ...updates } : tc
    ),
  })),
  
  setConnected: (connected) => set({ isConnected: connected }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  clearMessages: () => set({ messages: [], thoughts: [], toolCalls: [] }),
}));

/**
 * useChat Hook
 * 
 * 核心功能:
 * - 发送消息到后端API
 * - 监听SSE事件流
 * - 更新Zustand状态
 * - 处理文件上传
 */
export const useChat = () => {
  const {
    messages,
    thoughts,
    toolCalls,
    isConnected,
    isLoading,
    error,
    addMessage,
    addThought,
    addToolCall,
    updateToolCall,
    setConnected,
    setLoading,
    setError,
    clearMessages,
  } = useChatStore();
  
  /**
   * 发送消息
   */
  const sendMessage = async (
    text: string,
    files: File[] = [],
    threadId: string = 'default_session',
    source: string = 'user'
  ) => {
    try {
      setLoading(true);
      setError(null);
      
      // 1. 如果有文件,先上传文件
      let fileUrls: string[] = [];
      if (files.length > 0) {
        // TODO: 实现文件上传API
        // fileUrls = await uploadFiles(files);
        console.log('Files to upload:', files);
      }
      
      // 2. 添加用户消息到UI
      const userMessage: Message = {
        id: `msg-${Date.now()}`,
        timestamp: new Date().toISOString(),
        type: 'message',
        role: 'user',
        source,
        content: text,
        metadata: {
          files: fileUrls,
        },
      };
      addMessage(userMessage);
      
      // 3. 构造请求体
      const requestBody = {
        message: text,
        thread_id: threadId,
        source,
        metadata: {
          files: fileUrls,
          user_agent: navigator.userAgent,
        },
      };
      
      // 4. 发送POST请求到 /api/chat/stream
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // 5. 处理SSE流
      setConnected(true);
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      if (!reader) {
        throw new Error('Response body is null');
      }
      
      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          setConnected(false);
          setLoading(false);
          break;
        }
        
        // 解码数据
        buffer += decoder.decode(value, { stream: true });
        
        // 按行分割
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // 保留最后一行(可能不完整)
        
        for (const line of lines) {
          if (line.startsWith('event:')) {
            // 事件类型
            continue;
          }
          
          if (line.startsWith('data:')) {
            try {
              const data = JSON.parse(line.slice(5).trim());
              handleSSEEvent(data);
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } catch (err) {
      console.error('Error sending message:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setLoading(false);
      setConnected(false);
    }
  };
  
  /**
   * 处理SSE事件
   */
  const handleSSEEvent = (data: any) => {
    const { type } = data;
    
    switch (type) {
      case 'message':
        // Agent消息
        addMessage({
          id: data.id || `msg-${Date.now()}`,
          timestamp: data.timestamp || new Date().toISOString(),
          type: 'message',
          role: data.role || 'assistant',
          source: data.source || 'agent',
          content: data.content || '',
          metadata: data.metadata,
          // Generative UI
          component: data.component,
          componentProps: data.componentProps,
        });
        break;
      
      case 'thought':
        // 思维链
        addThought({
          id: data.id || `thought-${Date.now()}`,
          timestamp: data.timestamp || new Date().toISOString(),
          content: data.content || '',
          status: data.status || 'thinking',
        });
        break;
      
      case 'tool':
        // 工具调用
        if (data.status === 'calling') {
          addToolCall({
            id: data.id || `tool-${Date.now()}`,
            timestamp: data.timestamp || new Date().toISOString(),
            tool_name: data.tool_name || '',
            status: 'calling',
            input: data.input,
          });
        } else {
          updateToolCall(data.id, {
            status: data.status,
            output: data.output,
            error: data.error,
          });
        }
        break;
      
      case 'system':
        // 系统日志
        console.log('[System]', data.content);
        break;
      
      default:
        console.warn('Unknown SSE event type:', type);
    }
  };
  
  return {
    messages,
    thoughts,
    toolCalls,
    isConnected,
    isLoading,
    error,
    sendMessage,
    clearMessages,
  };
};
