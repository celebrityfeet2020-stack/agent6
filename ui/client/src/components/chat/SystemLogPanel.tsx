import { useState, useEffect, useRef } from "react";
import { Terminal, Activity, Filter, Brain, Wrench, AlertCircle, Info, Copy } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { DropdownMenu, DropdownMenuContent, DropdownMenuCheckboxItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

type LogType = "system" | "thought" | "tool" | "error";

type LogEntry = {
  id: string;
  timestamp: string;
  type: LogType;
  content: string;
  details?: string;
  status?: "running" | "completed" | "failed";
};

export function SystemLogPanel() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filters, setFilters] = useState<Record<LogType, boolean>>({
    system: true,
    thought: true,
    tool: true,
    error: true
  });
  const scrollRef = useRef<HTMLDivElement>(null);

  // Mock data generation
  useEffect(() => {
    const initialLogs: LogEntry[] = [
      { id: "1", timestamp: new Date().toLocaleTimeString(), type: "system", content: "M3 Agent System 初始化完成" },
      { id: "2", timestamp: new Date().toLocaleTimeString(), type: "thought", content: "接收到用户指令，正在分析意图...", status: "completed" },
      { id: "3", timestamp: new Date().toLocaleTimeString(), type: "tool", content: "调用工具: web_search (query='M3 Agent')", status: "running" },
    ];
    setLogs(initialLogs);

    const interval = setInterval(() => {
      if (Math.random() > 0.6) {
        const types: LogType[] = ["system", "thought", "tool", "error"];
        const type = types[Math.floor(Math.random() * types.length)];
        
        let content = "";
        if (type === "thought") content = "正在规划下一步行动...";
        else if (type === "tool") content = `执行工具调用: ${Math.random() > 0.5 ? "web_search" : "rpa_click"}`;
        else if (type === "error") content = "连接超时，正在重试...";
        else content = "系统状态检查正常";

        const newLog: LogEntry = {
          id: Date.now().toString(),
          timestamp: new Date().toLocaleTimeString(),
          type,
          content,
          status: type === "tool" || type === "thought" ? "running" : undefined
        };
        setLogs(prev => [...prev.slice(-199), newLog]);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const filteredLogs = logs.filter(log => filters[log.type]);

  const getIcon = (type: LogType) => {
    switch (type) {
      case "thought": return <Brain className="w-3.5 h-3.5 text-purple-400" />;
      case "tool": return <Wrench className="w-3.5 h-3.5 text-orange-400" />;
      case "error": return <AlertCircle className="w-3.5 h-3.5 text-red-400" />;
      default: return <Info className="w-3.5 h-3.5 text-blue-400" />;
    }
  };

  const copyCurl = (log: LogEntry) => {
    // Extract tool name and args from content (simplified for demo)
    // In real app, use structured metadata
    const curl = `curl -X POST http://localhost:8000/api/v1/tools/execute \\
  -H "Content-Type: application/json" \\
  -d '{"tool": "unknown", "args": {}}'`;
    navigator.clipboard.writeText(curl);
  };

  return (
    <div className="h-full flex flex-col bg-background/95 backdrop-blur border-b border-border/50">
      {/* Header */}
      <div className="h-9 flex items-center justify-between px-4 border-b border-border/20 bg-secondary/20 shrink-0">
        <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
          <Terminal className="w-3.5 h-3.5" />
          <span className="font-bold">系统日志 & 思维链</span>
          <div className="flex items-center gap-1 ml-2 px-1.5 py-0.5 rounded-full bg-primary/10 text-primary">
            <Activity className="w-3 h-3" />
            <span>运行中</span>
          </div>
        </div>
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-6 px-2 text-xs gap-1.5 text-muted-foreground hover:text-foreground">
              <Filter className="w-3 h-3" />
              筛选
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-40">
            <DropdownMenuCheckboxItem checked={filters.thought} onCheckedChange={c => setFilters(f => ({...f, thought: !!c}))}>
              思维链 (CoT)
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem checked={filters.tool} onCheckedChange={c => setFilters(f => ({...f, tool: !!c}))}>
              工具调用
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem checked={filters.system} onCheckedChange={c => setFilters(f => ({...f, system: !!c}))}>
              系统日志
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem checked={filters.error} onCheckedChange={c => setFilters(f => ({...f, error: !!c}))}>
              错误信息
            </DropdownMenuCheckboxItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Log Stream */}
      <div className="flex-1 overflow-hidden bg-[#0a0e14]">
        <ScrollArea className="h-full w-full">
          <div className="p-4 space-y-1 font-mono text-xs" ref={scrollRef}>
            {filteredLogs.map((log) => (
              <div 
                key={log.id} 
                className={cn(
                  "flex gap-3 p-1.5 rounded border-l-2 transition-all group relative",
                  log.type === "thought" && "bg-purple-500/5 border-purple-500/50 text-purple-100",
                  log.type === "tool" && "bg-orange-500/5 border-orange-500/50 text-orange-100",
                  log.type === "error" && "bg-red-500/5 border-red-500/50 text-red-100",
                  log.type === "system" && "border-transparent text-muted-foreground hover:bg-white/5"
                )}
              >
                <span className="text-muted-foreground/40 min-w-[70px] select-none">{log.timestamp}</span>
                <div className="flex items-center gap-2 min-w-[24px] justify-center">
                  {getIcon(log.type)}
                </div>
                <div className="flex-1 break-all">
                  <span className="font-bold mr-2 uppercase tracking-wider text-[10px] opacity-70">
                    [{log.type}]
                  </span>
                  {log.content}
                  {log.status === "running" && (
                    <span className="ml-2 inline-block w-1.5 h-1.5 bg-current rounded-full animate-pulse" />
                  )}
                </div>
                
                {log.type === 'tool' && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-5 w-5 absolute right-2 top-1.5 opacity-0 group-hover:opacity-100 transition-opacity bg-background/20 hover:bg-background/40"
                        onClick={() => copyCurl(log)}
                      >
                        <Copy className="w-3 h-3 text-muted-foreground hover:text-primary" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Copy cURL</TooltipContent>
                  </Tooltip>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
