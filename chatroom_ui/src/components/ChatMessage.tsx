import React from 'react';
import { User, Bot, Code, Tv, Users } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import type { Message } from '../hooks/useChat';
import { GenerativeComponent } from './GenerativeComponent';

interface ChatMessageProps {
  message: Message;
}

/**
 * 聊天消息组件
 * 
 * 功能:
 * - 根据source显示不同角色的消息
 * - 支持Markdown渲染
 * - 支持代码高亮
 * - 支持Generative UI
 */
export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  // 获取角色信息
  const getRoleInfo = (source?: string, role?: string) => {
    if (role === 'user' || source === 'user') {
      return {
        icon: <User className="w-5 h-5" />,
        name: '用户',
        bgColor: 'bg-blue-500',
      };
    }
    
    if (source === 'api') {
      return {
        icon: <Code className="w-5 h-5" />,
        name: 'API调用',
        bgColor: 'bg-purple-500',
      };
    }
    
    if (source === 'admin') {
      return {
        icon: <Users className="w-5 h-5" />,
        name: '管理员',
        bgColor: 'bg-orange-500',
      };
    }
    
    if (source === 'livestream') {
      return {
        icon: <Tv className="w-5 h-5" />,
        name: '直播数字人',
        bgColor: 'bg-pink-500',
      };
    }
    
    if (source === 'fleet') {
      return {
        icon: <Users className="w-5 h-5" />,
        name: '舰队Agent',
        bgColor: 'bg-teal-500',
      };
    }
    
    // 默认: Agent
    return {
      icon: <Bot className="w-5 h-5" />,
      name: 'M3 Agent',
      bgColor: 'bg-green-500',
    };
  };
  
  const roleInfo = getRoleInfo(message.source, message.role);
  const isUser = message.role === 'user' || message.source === 'user';
  
  // 格式化时间
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  };
  
  return (
    <div className={`chat-message ${isUser ? 'chat-message-user' : 'chat-message-agent'}`}>
      {/* 头像 */}
      <div className={`message-avatar ${roleInfo.bgColor}`}>
        {roleInfo.icon}
      </div>
      
      {/* 消息内容 */}
      <div className="message-content-wrapper">
        {/* 头部 */}
        <div className="message-header">
          <span className="message-name">{roleInfo.name}</span>
          <span className="message-time">{formatTime(message.timestamp)}</span>
        </div>
        
        {/* 内容 */}
        <div className="message-content">
          {/* Generative UI */}
          {message.component ? (
            <GenerativeComponent
              component={message.component}
              props={message.componentProps || {}}
            />
          ) : (
            /* Markdown渲染 */
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={vscDarkPlus}
                      language={match[1]}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>
        
        {/* 元数据 */}
        {message.metadata && Object.keys(message.metadata).length > 0 && (
          <div className="message-metadata">
            {message.metadata.user_name && (
              <span className="metadata-item">👤 {message.metadata.user_name}</span>
            )}
            {message.metadata.device && (
              <span className="metadata-item">📱 {message.metadata.device}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
