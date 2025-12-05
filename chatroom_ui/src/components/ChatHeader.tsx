import React from 'react';
import { Settings, RotateCcw, ExternalLink } from 'lucide-react';

interface ChatHeaderProps {
  threadId: string;
  onReset?: () => void;
  onSettings?: () => void;
}

/**
 * 聊天室头部组件
 * 
 * 显示:
 * - 标题
 * - 当前thread_id
 * - 操作按钮 (重置、设置、返回管理面板)
 */
export const ChatHeader: React.FC<ChatHeaderProps> = ({
  threadId,
  onReset,
  onSettings,
}) => {
  return (
    <header className="flex items-center justify-between p-4 bg-dark-surface border-b border-dark-border">
      {/* 左侧: 标题和thread_id */}
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold text-primary-400">
          M3 Agent 统一聊天室
        </h1>
        
        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-400">会话:</span>
          <code className="px-2 py-1 bg-dark-bg rounded text-primary-300">
            {threadId}
          </code>
          
          {threadId === 'default_session' && (
            <span className="px-2 py-1 bg-green-900/30 text-green-400 rounded text-xs">
              共享窗口
            </span>
          )}
        </div>
      </div>
      
      {/* 右侧: 操作按钮 */}
      <div className="flex items-center gap-2">
        {/* 重置按钮 */}
        {onReset && (
          <button
            onClick={onReset}
            className="btn-secondary flex items-center gap-2"
            title="重置会话"
          >
            <RotateCcw className="w-4 h-4" />
            <span className="hidden sm:inline">重置</span>
          </button>
        )}
        
        {/* 设置按钮 */}
        {onSettings && (
          <button
            onClick={onSettings}
            className="btn-secondary flex items-center gap-2"
            title="设置"
          >
            <Settings className="w-4 h-4" />
            <span className="hidden sm:inline">设置</span>
          </button>
        )}
        
        {/* 返回管理面板 */}
        <a
          href="/admin"
          className="btn-secondary flex items-center gap-2"
          title="返回管理面板"
        >
          <ExternalLink className="w-4 h-4" />
          <span className="hidden sm:inline">管理面板</span>
        </a>
      </div>
    </header>
  );
};
