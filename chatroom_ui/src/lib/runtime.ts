import { useLangGraphRuntime } from "@assistant-ui/react-langgraph";

/**
 * M3 Agent LangGraph运行时配置
 * 
 * 核心设计:
 * - 默认使用 "default_session" thread_id
 * - 支持通过URL参数切换thread_id
 * - 所有用户/API/Admin共享同一个会话
 */

export function useM3AgentRuntime() {
  // 从URL获取thread_id,默认为default_session
  const urlParams = new URLSearchParams(window.location.search);
  const threadId = urlParams.get('thread_id') || 'default_session';
  
  // 获取后端API地址
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8888';
  
  // 配置LangGraph运行时
  const runtime = useLangGraphRuntime({
    graphId: "m3-agent",  // 对应后端的assistant_id
    apiUrl: apiUrl,
    threadId: threadId,
    
    // 流式配置
    stream: true,
    streamMode: ["messages", "updates", "debug"],
    
    // 自定义请求头
    headers: {
      "Content-Type": "application/json",
    },
    
    // 错误处理
    onError: (error) => {
      console.error("LangGraph Runtime Error:", error);
    },
  });
  
  return {
    runtime,
    threadId,
    apiUrl,
  };
}

/**
 * 格式化时间为北京时间
 */
export function toBeijingTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    // 转换为北京时间 (UTC+8)
    const beijingTime = new Date(date.getTime() + (8 * 60 * 60 * 1000));
    
    const year = beijingTime.getUTCFullYear();
    const month = String(beijingTime.getUTCMonth() + 1).padStart(2, '0');
    const day = String(beijingTime.getUTCDate()).padStart(2, '0');
    const hours = String(beijingTime.getUTCHours()).padStart(2, '0');
    const minutes = String(beijingTime.getUTCMinutes()).padStart(2, '0');
    const seconds = String(beijingTime.getUTCSeconds()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  } catch (error) {
    return isoString;
  }
}

/**
 * 获取角色标识
 */
export function getRoleLabel(source: string): string {
  const roleMap: Record<string, string> = {
    user: "用户",
    api: "API",
    admin: "管理员",
    livestream: "直播间",
    fleet: "舰队",
  };
  return roleMap[source] || source;
}

/**
 * 获取角色颜色
 */
export function getRoleColor(source: string): string {
  const colorMap: Record<string, string> = {
    user: "text-blue-400",
    api: "text-green-400",
    admin: "text-red-400",
    livestream: "text-purple-400",
    fleet: "text-yellow-400",
  };
  return colorMap[source] || "text-gray-400";
}

/**
 * 获取角色图标
 */
export function getRoleIcon(source: string): string {
  const iconMap: Record<string, string> = {
    user: "👤",
    api: "🤖",
    admin: "👨‍💼",
    livestream: "📺",
    fleet: "🚢",
  };
  return iconMap[source] || "💬";
}
