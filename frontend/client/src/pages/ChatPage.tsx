import { AssistantRuntimeProvider, useAssistantRuntime } from "@assistant-ui/react";
import { useM3AgentRuntime } from "@/lib/runtime";
import { M3Thread } from "@/components/chat/M3Thread";
import { M3Composer } from "@/components/chat/M3Composer";
import { SystemLogPanel } from "@/components/chat/SystemLogPanel";
import { useState, useEffect } from "react";
import { RefreshCw, Wifi, WifiOff, RotateCcw, Activity, Trash2, ChevronUp, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { useSoundEffects } from "@/hooks/useSoundEffects";
import { useMediaQuery } from "@/hooks/use-media-query";
import { NameSettingsDialog, useNameSettings } from "@/components/settings/NameSettings";

// Separate component for Header Actions to access runtime context if needed
const HeaderActions = ({ isLive, setIsLive, handleManualRefresh }: any) => {
  const runtime = useAssistantRuntime();
  const { playClick } = useSoundEffects();
  const isMobile = useMediaQuery("(max-width: 768px)");

  const handleQuickAction = (command: string) => {
    playClick();
    // In a real app, we would send this command to the runtime
    // runtime.append(command); 
    console.log("Executing command:", command);
  };

  return (
    <div className="flex items-center gap-3">
      {/* Quick Actions - Hidden on mobile to save space */}
      {!isMobile && (
        <div className="flex items-center gap-1 mr-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button 
                variant="ghost" 
                size="sm" 
                className="h-7 px-2 text-[10px] gap-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10"
                onClick={() => handleQuickAction("/reset_memory")}
              >
                <RotateCcw className="w-3 h-3" />
                重置记忆
              </Button>
            </TooltipTrigger>
            <TooltipContent>清除 Agent 短期记忆</TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button 
                variant="ghost" 
                size="sm" 
                className="h-7 px-2 text-[10px] gap-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10"
                onClick={() => handleQuickAction("/status")}
              >
                <Activity className="w-3 h-3" />
                查看状态
              </Button>
            </TooltipTrigger>
            <TooltipContent>检查系统运行状态</TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button 
                variant="ghost" 
                size="sm" 
                className="h-7 px-2 text-[10px] gap-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                onClick={() => handleQuickAction("/clear_context")}
              >
                <Trash2 className="w-3 h-3" />
                清空上下文
              </Button>
            </TooltipTrigger>
            <TooltipContent>清空当前对话历史</TooltipContent>
          </Tooltip>
        </div>
      )}

      <div className="h-4 w-px bg-border/50" />
      
      <Tooltip>
        <TooltipTrigger asChild>
          <Button 
            variant="ghost" 
            size="icon" 
            className={cn("h-7 w-7", isLive ? "text-green-500" : "text-muted-foreground")}
            onClick={() => setIsLive(!isLive)}
          >
            {isLive ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>实时同步 {isLive ? '开启' : '关闭'}</p>
        </TooltipContent>
      </Tooltip>
      
      <Tooltip>
        <TooltipTrigger asChild>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-7 w-7 text-muted-foreground hover:text-foreground"
            onClick={handleManualRefresh}
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>强制刷新页面</p>
        </TooltipContent>
      </Tooltip>
    </div>
  );
};

export default function ChatPage() {
  const runtime = useM3AgentRuntime();
  const [isLive, setIsLive] = useState(true);
  const [lastSync, setLastSync] = useState<Date>(new Date());
  const isMobile = useMediaQuery("(max-width: 768px)");
  const [showLogsMobile, setShowLogsMobile] = useState(false);
  const { names } = useNameSettings();
  
  // Auto-refresh logic to sync API messages
  useEffect(() => {
    if (!isLive) return;
    
    const interval = setInterval(() => {
      setLastSync(new Date());
    }, 5000);
    
    return () => clearInterval(interval);
  }, [isLive]);

  const handleManualRefresh = () => {
    window.location.reload(); 
  };

  return (
    <div className="h-screen w-full bg-background flex flex-col overflow-hidden">
      <AssistantRuntimeProvider runtime={runtime}>
        {/* Header / Status Bar */}
        <header className="h-12 border-b border-border/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex items-center justify-between px-4 z-10 shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            <span className="text-xs font-mono font-bold text-primary tracking-widest">M3 AGENT // 指挥中心</span>
            
            {!isMobile && (
              <div className="ml-4 flex items-center gap-1.5 text-[10px] font-mono text-muted-foreground">
                <span>同步:</span>
                <span className="text-foreground">{lastSync.toLocaleTimeString()}</span>
              </div>
            )}
          </div>
          
          <TooltipProvider>
            <div className="flex items-center gap-2">
              <NameSettingsDialog />
              <HeaderActions 
                isLive={isLive} 
                setIsLive={setIsLive} 
                handleManualRefresh={handleManualRefresh} 
              />
            </div>
          </TooltipProvider>
        </header>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-h-0 relative">
          {isMobile ? (
            // Mobile Layout: Stacked with toggle
            <div className="flex-1 flex flex-col min-h-0 relative">
              {/* Log Toggle Button */}
              <div className="absolute top-2 right-2 z-20">
                <Button 
                  variant="secondary" 
                  size="sm" 
                  className="h-7 text-xs opacity-80 hover:opacity-100 shadow-sm"
                  onClick={() => setShowLogsMobile(!showLogsMobile)}
                >
                  {showLogsMobile ? <ChevronUp className="w-3 h-3 mr-1" /> : <ChevronDown className="w-3 h-3 mr-1" />}
                  {showLogsMobile ? "收起日志" : "展开日志"}
                </Button>
              </div>

              {/* Logs Panel (Collapsible) */}
              <div 
                className={cn(
                  "transition-all duration-300 ease-in-out overflow-hidden border-b border-border/50 bg-background/95 backdrop-blur z-10 absolute top-0 left-0 right-0",
                  showLogsMobile ? "h-[40%]" : "h-0"
                )}
              >
                <SystemLogPanel />
              </div>

              {/* Chat Thread */}
              <div className="flex-1 h-full pt-0">
                <M3Thread 
                  userRoleName={names.userRoleName}
                  apiRoleName={names.apiRoleName}
                  agentRoleName={names.agentRoleName}
                />
              </div>
            </div>
          ) : (
            // Desktop Layout: Resizable Panels
            <div className="flex-1 min-h-0">
              <PanelGroup direction="vertical">
                {/* Top Panel: System Logs & CoT */}
                <Panel defaultSize={40} minSize={20} className="bg-background/50">
                  <SystemLogPanel />
                </Panel>
                
                <PanelResizeHandle className="h-1.5 bg-border/30 hover:bg-primary/50 transition-colors cursor-row-resize flex items-center justify-center group z-20">
                  <div className="w-16 h-1 rounded-full bg-border/50 group-hover:bg-primary/80 transition-colors" />
                </PanelResizeHandle>
                
                {/* Middle Panel: Chat Thread */}
                <Panel defaultSize={60} minSize={30}>
                  <M3Thread 
                    userRoleName={names.userRoleName}
                    apiRoleName={names.apiRoleName}
                    agentRoleName={names.agentRoleName}
                  />
                </Panel>
              </PanelGroup>
            </div>
          )}
          
          {/* Bottom Area: Composer (Fixed) */}
          <div className="shrink-0 z-30 bg-background border-t border-border/50">
            <M3Composer />
          </div>
        </div>
      </AssistantRuntimeProvider>
    </div>
  );
}
