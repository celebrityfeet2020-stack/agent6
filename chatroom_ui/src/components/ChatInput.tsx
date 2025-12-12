import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (text: string, files: File[], source?: string) => void;
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
  onSendMessage,
  disabled = false,
  placeholder = "输入消息...",
}) => {
  const [message, setMessage] = useState('');
  const [selectedRole, setSelectedRole] = useState('user');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // 角色选项
  const roleOptions = [
    { value: 'user', label: '👤 用户' },
    { value: 'admin', label: '👑 管理员' },
    { value: 'n8_workflow', label: '⚙️ N8工作流' },
    { value: 'digital_human_guest', label: '🤖 数字人访客' },
    { value: 'git_committer', label: '👨‍💻 Git提交者' },
    { value: 'fleet', label: '🛥️ 舰队Agent' },
  ];
  
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
      onSendMessage(trimmedMessage, [], selectedRole);
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
    <div className="flex flex-col gap-2 p-4 bg-dark-surface border-t border-dark-border">
      {/* 角色选择器 */}
      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-400">角色:</label>
        <select
          value={selectedRole}
          onChange={(e) => setSelectedRole(e.target.value)}
          disabled={disabled}
          className="px-3 py-1 bg-dark-bg border border-dark-border rounded text-sm text-gray-200 focus:outline-none focus:border-primary-500"
        >
          {roleOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      
      {/* 输入区 */}
      <div className="flex items-end gap-2">
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
    </div>
  );
};
