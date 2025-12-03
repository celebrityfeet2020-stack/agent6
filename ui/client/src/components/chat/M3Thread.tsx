import { 
  ThreadPrimitive, 
  MessagePrimitive, 
  ActionBarPrimitive,
  useMessage
} from "@assistant-ui/react";
import { User, Bot, Copy, Check, Terminal } from "lucide-react";
import { MarkdownText } from "./MarkdownText";
import { WebSearchTool } from "../tools/WebSearchTool";
import { RPATool } from "../tools/RPATool";
import { FileSyncTool } from "../tools/FileSyncTool";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

type M3ThreadProps = {
  userRoleName?: string;
  agentRoleName?: string;
  apiRoleName?: string;
};

export const M3Thread = ({ 
  userRoleName = "Kori", 
  agentRoleName = "M3 AGENT",
  apiRoleName = "Kori-API"
}: M3ThreadProps) => {
  return (
    <ThreadPrimitive.Root className="h-full flex flex-col bg-background">
      <ThreadPrimitive.Viewport className="flex-1 overflow-y-auto scroll-smooth px-4 py-4 md:px-8">
        <ThreadPrimitive.Empty>
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground space-y-4">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20 animate-pulse">
              <Bot className="w-8 h-8 text-primary" />
            </div>
            <div className="text-center">
              <h2 className="text-2xl font-bold text-foreground tracking-tight font-mono">M3 AGENT SYSTEM</h2>
              <p className="text-sm mt-2 font-mono text-primary/60">Cyber-Tactical Command Interface v2.0.0</p>
              <p className="text-xs mt-1 font-mono text-muted-foreground">系统在线。等待指令。</p>
            </div>
          </div>
        </ThreadPrimitive.Empty>

        <ThreadPrimitive.Messages components={{
          UserMessage: () => {
            const message = useMessage();
            // Check if message is from API (mock logic for now, relies on metadata if available)
            // In a real scenario, we'd check message.metadata?.source === 'api'
            const isApi = (message as any).metadata?.source === 'api';
            const displayName = isApi ? apiRoleName : userRoleName;
            
            return (
              <MessagePrimitive.Root className="flex w-full justify-end mb-6 group">
                <div className="flex flex-col items-end max-w-[85%] md:max-w-[75%]">
                  <div className="flex items-center gap-2 mb-1 mr-1">
                    <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">
                      {displayName}
                    </span>
                    {isApi && <Terminal className="w-3 h-3 text-muted-foreground" />}
                  </div>
                  
                  <div className={cn(
                    "relative px-5 py-3.5 rounded-2xl rounded-tr-sm shadow-sm text-sm leading-relaxed",
                    "bg-secondary text-secondary-foreground border border-border/50", // Darker, eye-friendly
                    "transition-all duration-200 hover:shadow-md hover:border-primary/20"
                  )}>
                    <MessagePrimitive.Content />
                  </div>
                </div>
              </MessagePrimitive.Root>
            );
          },
          
          AssistantMessage: () => (
            <MessagePrimitive.Root className="flex w-full justify-start mb-8 group">
              <div className="flex gap-4 max-w-[90%] md:max-w-[85%]">
                <Avatar className="w-8 h-8 mt-1 border border-primary/20 bg-card shadow-sm">
                  <AvatarFallback className="bg-primary/5 text-primary">AI</AvatarFallback>
                  <AvatarImage src="/bot-avatar.png" />
                </Avatar>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5 ml-1">
                    <span className="text-[10px] font-mono text-primary font-bold uppercase tracking-wider">
                      {agentRoleName}
                    </span>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <ActionBarPrimitive.Root>
                        <ActionBarPrimitive.Copy asChild>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button className="p-1 hover:bg-muted rounded text-muted-foreground hover:text-foreground transition-colors">
                                <Copy className="w-3 h-3" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent>复制内容</TooltipContent>
                          </Tooltip>
                        </ActionBarPrimitive.Copy>
                      </ActionBarPrimitive.Root>
                    </div>
                  </div>
                  
                  <div className="bg-card border border-border/50 px-5 py-4 rounded-2xl rounded-tl-sm shadow-sm">
                    <MessagePrimitive.Content components={{ 
                      Text: MarkdownText,
                      tools: {
                        by_name: {
                          web_search: WebSearchTool,
                          rpa_tool: RPATool,
                          file_sync_tool: FileSyncTool
                        }
                      }
                    }} />
                  </div>
                </div>
              </div>
            </MessagePrimitive.Root>
          ),
        }} />
      </ThreadPrimitive.Viewport>
    </ThreadPrimitive.Root>
  );
};
