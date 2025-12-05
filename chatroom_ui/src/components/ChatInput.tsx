import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

/**
 * 聊天输入组件
 * 
 * 功能:
 * - 多行文本输入
 * - 支持Enter发送, Shift+Enter换行
 * - 自动调整高度
 * - 发送按钮
 */
export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  disabled = false,
  placeholder = "输入消息...",
}) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // 自动调整textarea高度
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);
  
  // 处理发送
  const handleSend = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !disabled) {
      onSend(trimmedMessage);
      setMessage('');
      
      // 重置textarea高度
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };
  
  // 处理键盘事件
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };
  
  return (
    <div className="flex items-end gap-2 p-4 bg-dark-surface border-t border-dark-border">
      {/* 文本输入区 */}
      <textarea
        ref={textareaRef}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className="flex-1 input-field resize-none max-h-32 min-h-[44px]"
        style={{ 
          scrollbarWidth: 'thin',
        }}
      />
      
      {/* 发送按钮 */}
      <button
        onClick={handleSend}
        disabled={disabled || !message.trim()}
        className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 h-[44px]"
        title="发送 (Enter)"
      >
        {disabled ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : (
          <Send className="w-5 h-5" />
        )}
        <span className="hidden sm:inline">发送</span>
      </button>
    </div>
  );
};
