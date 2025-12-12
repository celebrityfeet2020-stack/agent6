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
  // 获取角色信息 (支持动态角色)
  const getRoleInfo = (source?: string, role?: string) => {
    // 预定义角色映射
    const roleMap: Record<string, { icon: JSX.Element; name: string; bgColor: string }> = {
      user: {
        icon: <User className="w-5 h-5" />,
        name: '用户',
        bgColor: 'bg-blue-500',
      },
      admin: {
        icon: <Users className="w-5 h-5" />,
        name: '管理员',
        bgColor: 'bg-red-500',
      },
      assistant: {
        icon: <Bot className="w-5 h-5" />,
        name: 'M3 Agent',
        bgColor: 'bg-green-500',
      },
      api: {
        icon: <Code className="w-5 h-5" />,
        name: 'API调用',
        bgColor: 'bg-purple-500',
      },
      livestream: {
        icon: <Tv className="w-5 h-5" />,
        name: '直播数字人',
        bgColor: 'bg-pink-500',
      },
      digital_human_guest: {
        icon: <Tv className="w-5 h-5" />,
        name: '数字人访客',
        bgColor: 'bg-purple-600',
      },
      fleet: {
        icon: <Users className="w-5 h-5" />,
        name: '舰队Agent',
        bgColor: 'bg-teal-500',
      },
      n8_workflow: {
        icon: <Code className="w-5 h-5" />,
        name: 'N8工作流',
        bgColor: 'bg-yellow-500',
      },
      git_committer: {
        icon: <Code className="w-5 h-5" />,
        name: 'Git提交者',
        bgColor: 'bg-orange-600',
      },
    };
    
    // 优先使用source,其次使用role
    const roleKey = source || role || 'assistant';
    
    // 如果找到预定义角色,返回
    if (roleMap[roleKey]) {
      return roleMap[roleKey];
    }
    
    // 如果是未知角色,动态生成
    const colors = ['bg-indigo-500', 'bg-cyan-500', 'bg-lime-500', 'bg-amber-500', 'bg-rose-500'];
    const colorIndex = roleKey.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % colors.length;
    
    return {
      icon: <Bot className="w-5 h-5" />,
      name: roleKey.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
      bgColor: colors[colorIndex],
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
