import { useLocalRuntime } from "@assistant-ui/react";
import { useState, useEffect } from "react";
import { WebSocketClient, ChatMessage } from "./websocket-client";

const THREAD_ID = "default"; // 固定thread_id

export const useM3AgentRuntime = () => {
  const [wsClient] = useState(() => new WebSocketClient(THREAD_ID));
  const [messages, setMessages] = useState<any[]>([
    {
      id: "welcome",
      role: "assistant",
      content: [
        {
          type: "text",
          text: "M3 Agent System v2.2 已就绪。三角聊天室已启动，支持User/API/Agent三方实时对话。",
        },
      ],
    },
  ]);

  // 初始化WebSocket连接
  useEffect(() => {
    // 连接WebSocket
    wsClient.connect();

    // 监听新消息
    wsClient.on("message", (data: ChatMessage) => {
      console.log("[Runtime] New message from WebSocket:", data);
      
      // 将WebSocket消息转换为assistant-ui格式
      const newMessage = {
        id: `msg-${Date.now()}`,
        role: data.role === "user" ? "user" : "assistant",
        content: [
          {
            type: "text",
            text: data.content,
          },
        ],
        metadata: {
          source: data.source,
          timestamp: data.timestamp,
        },
      };

      setMessages((prev) => [...prev, newMessage]);
    });

    // 监听连接状态
    wsClient.on("connected", (data) => {
      console.log("[Runtime] WebSocket connected:", data);
    });

    wsClient.on("disconnected", () => {
      console.log("[Runtime] WebSocket disconnected");
    });

    // 加载历史消息
    loadHistory();

    return () => {
      wsClient.disconnect();
    };
  }, [wsClient]);

  // 加载历史消息
  const loadHistory = async () => {
    try {
      const response = await fetch(`/api/threads/${THREAD_ID}/history?limit=100`);
      const data = await response.json();
      
      if (data.messages && data.messages.length > 0) {
        const historyMessages = data.messages.map((msg: any) => ({
          id: `history-${msg.id}`,
          role: msg.content.startsWith("[user]") ? "user" : "assistant",
          content: [
            {
              type: "text",
              text: msg.content.replace(/^\[(user|assistant)\]\s*/, ""),
            },
          ],
          metadata: {
            source: msg.source,
            timestamp: msg.timestamp,
          },
        }));

        setMessages((prev) => [...prev, ...historyMessages]);
      }
    } catch (error) {
      console.error("[Runtime] Failed to load history:", error);
    }
  };

  // @ts-ignore - Bypassing type check to focus on logic
  const runtime = useLocalRuntime({
    initialMessages: messages,
    adapter: {
      async onNew(message: any) {
        if (message.content[0]?.type !== "text") return;
        
        const userText = message.content[0].text;
        
        try {
          // 发送消息到后端
          const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              message: userText,
              thread_id: THREAD_ID,
              source: "user",
            }),
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const data = await response.json();
          console.log("[Runtime] Chat response:", data);

          // WebSocket会自动推送消息，不需要手动添加
        } catch (error) {
          console.error("[Runtime] Failed to send message:", error);
        }
      },
    },
  });

  return runtime;
};
