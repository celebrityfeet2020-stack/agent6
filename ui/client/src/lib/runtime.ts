import { useLocalRuntime } from "@assistant-ui/react";
import { SSEClient } from "./sse-adapter";
import { useState } from "react";

export const useM3AgentRuntime = () => {
  const [sseClient] = useState(() => new SSEClient('/api/v1/chat/stream'));

  // @ts-ignore - Bypassing type check to focus on logic
  const runtime = useLocalRuntime({
    initialMessages: [
      {
        id: "welcome",
        role: "assistant",
        content: [
          {
            type: "text",
            text: "M3 Agent System v3.5 已就绪。我是您的战术指挥助手 Qwen3-30B，请下达指令。",
          },
        ],
      },
    ],
    adapter: {
      async onNew(message: any) {
        if (message.content[0]?.type !== "text") return;
        
        const userText = message.content[0].text;
        
        // Connect to SSE stream
        sseClient.connect(userText);
        
        // Listen for message deltas
        sseClient.on('message', (data) => {
          if (data.delta) {
            // In a real implementation, we would update the message content incrementally here
            // For now, we log the delta to verify the stream is working
            console.log('Stream delta:', data.content);
          }
        });

        // Listen for tool calls
        sseClient.on('tool', (data) => {
          if (data.status === 'calling') {
            console.log('Tool call:', data);
          }
        });
      }
    }
  });

  return runtime;
};
