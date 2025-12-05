import React, { useState, useRef, useEffect } from 'react';
import { ChatHeader } from './components/ChatHeader';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { ThoughtChain } from './components/ThoughtChain';
import { Resizer } from './components/Resizer';
import { useChat } from './hooks/useChat';

/**
 * M3 Agent v6.0 主应用组件
 * 
 * 三层布局:
 * 1. 上层: 思维链 + 工具链
 * 2. 中层: 对话框
 * 3. 下层: 输入框
 * 
 * 特性:
 * - 可拖动分割线调整上下层比例
 * - 支持三方可见 (用户/API/Admin/直播/舰队)
 * - 支持Generative UI
 * - 支持文件上传 (全格式)
 */
function App() {
  const {
    messages,
    thoughts,
    toolCalls,
    isConnected,
    isLoading,
    error,
    sendMessage,
    clearMessages,
  } = useChat();
  
  // 布局状态
  const [topHeight, setTopHeight] = useState(200); // 上层高度 (px)
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // 自动滚动到最新消息
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // 处理发送消息
  const handleSendMessage = async (text: string, files: File[]) => {
    await sendMessage(text, files);
  };
  
  return (
    <div className="app-container">
      {/* 头部 */}
      <ChatHeader
        isConnected={isConnected}
        onClearMessages={clearMessages}
      />
      
      {/* 主内容区 */}
      <div className="app-content">
        {/* 上层: 思维链 + 工具链 */}
        <div
          className="thought-panel"
          style={{ height: `${topHeight}px` }}
        >
          <ThoughtChain thoughts={thoughts} toolCalls={toolCalls} />
        </div>
        
        {/* 可拖动分割线 */}
        <Resizer
          onResize={(deltaY) => {
            setTopHeight((prev) => Math.max(100, Math.min(600, prev + deltaY)));
          }}
        />
        
        {/* 中层: 对话框 */}
        <div className="messages-panel">
          {error && (
            <div className="error-banner">
              <p>❌ {error}</p>
            </div>
          )}
          
          {messages.length === 0 ? (
            <div className="messages-empty">
              <h2 className="text-2xl font-bold mb-4">欢迎使用 M3 Agent v6.0</h2>
              <p className="text-gray-500 mb-2">这是一个三方可见的单会话窗口</p>
              <p className="text-sm text-gray-400">
                所有人(用户/API/直播/舰队)默认共享同一个对话
              </p>
            </div>
          ) : (
            <div className="messages-list">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
          
          {isLoading && (
            <div className="loading-indicator">
              <div className="loading-spinner" />
              <span>Agent正在思考...</span>
            </div>
          )}
        </div>
        
        {/* 下层: 输入框 */}
        <div className="input-panel">
          <ChatInput
            onSendMessage={handleSendMessage}
            disabled={isLoading}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
