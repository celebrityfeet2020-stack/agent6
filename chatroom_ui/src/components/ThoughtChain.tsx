import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Brain, Wrench, CheckCircle, XCircle, Loader } from 'lucide-react';
import type { ThoughtStep, ToolCall } from '../hooks/useChat';

interface ThoughtChainProps {
  thoughts: ThoughtStep[];
  toolCalls: ToolCall[];
}

/**
 * 思维链和工具链可视化组件
 * 
 * 功能:
 * - 显示Agent的思维过程
 * - 显示工具调用的详细信息
 * - 可折叠的详细视图
 */
export const ThoughtChain: React.FC<ThoughtChainProps> = ({ thoughts, toolCalls }) => {
  const [expandedThoughts, setExpandedThoughts] = useState<Set<string>>(new Set());
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set());
  
  const toggleThought = (id: string) => {
    setExpandedThoughts((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };
  
  const toggleTool = (id: string) => {
    setExpandedTools((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };
  
  // 获取工具状态图标
  const getToolStatusIcon = (status: ToolCall['status']) => {
    switch (status) {
      case 'calling':
        return <Loader className="w-4 h-4 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
    }
  };
  
  // 格式化时间
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };
  
  if (thoughts.length === 0 && toolCalls.length === 0) {
    return (
      <div className="thought-chain-empty">
        <Brain className="w-8 h-8 text-gray-400 mx-auto mb-2" />
        <p className="text-sm text-gray-500">等待Agent思考...</p>
      </div>
    );
  }
  
  return (
    <div className="thought-chain-container">
      {/* 思维链 */}
      {thoughts.length > 0 && (
        <div className="thought-section">
          <div className="section-header">
            <Brain className="w-5 h-5" />
            <span>思维链</span>
            <span className="badge">{thoughts.length}</span>
          </div>
          
          <div className="thought-list">
            {thoughts.map((thought) => {
              const isExpanded = expandedThoughts.has(thought.id);
              const isLong = thought.content.length > 100;
              
              return (
                <div key={thought.id} className="thought-item">
                  <div className="thought-header">
                    <div className="thought-status">
                      {thought.status === 'thinking' ? (
                        <Loader className="w-4 h-4 animate-spin text-blue-500" />
                      ) : (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      )}
                    </div>
                    
                    <div className="thought-content">
                      <p className={isExpanded ? '' : 'line-clamp-2'}>
                        {thought.content}
                      </p>
                      
                      {isLong && (
                        <button
                          onClick={() => toggleThought(thought.id)}
                          className="thought-toggle"
                        >
                          {isExpanded ? '收起' : '展开'}
                        </button>
                      )}
                    </div>
                    
                    <span className="thought-time">{formatTime(thought.timestamp)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
      
      {/* 工具链 */}
      {toolCalls.length > 0 && (
        <div className="tool-section">
          <div className="section-header">
            <Wrench className="w-5 h-5" />
            <span>工具调用</span>
            <span className="badge">{toolCalls.length}</span>
          </div>
          
          <div className="tool-list">
            {toolCalls.map((tool) => {
              const isExpanded = expandedTools.has(tool.id);
              
              return (
                <div key={tool.id} className="tool-item">
                  <div className="tool-header" onClick={() => toggleTool(tool.id)}>
                    <div className="tool-status">
                      {getToolStatusIcon(tool.status)}
                    </div>
                    
                    <div className="tool-name">
                      <span className="font-medium">{tool.tool_name}</span>
                      <span className="tool-time">{formatTime(tool.timestamp)}</span>
                    </div>
                    
                    <button className="tool-expand">
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                  
                  {isExpanded && (
                    <div className="tool-details">
                      {/* 输入参数 */}
                      {tool.input && (
                        <div className="tool-detail-section">
                          <div className="detail-label">输入参数</div>
                          <pre className="detail-content">
                            {JSON.stringify(tool.input, null, 2)}
                          </pre>
                        </div>
                      )}
                      
                      {/* 输出结果 */}
                      {tool.output && (
                        <div className="tool-detail-section">
                          <div className="detail-label">输出结果</div>
                          <pre className="detail-content">
                            {typeof tool.output === 'string'
                              ? tool.output
                              : JSON.stringify(tool.output, null, 2)}
                          </pre>
                        </div>
                      )}
                      
                      {/* 错误信息 */}
                      {tool.error && (
                        <div className="tool-detail-section">
                          <div className="detail-label text-red-600">错误信息</div>
                          <pre className="detail-content text-red-600">
                            {tool.error}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
