import { makeAssistantToolUI } from "@assistant-ui/react";
import { Monitor, MousePointer, Keyboard, Loader2 } from "lucide-react";

type RPAArgs = {
  action: string;
  [key: string]: unknown;
};

type RPAResult = string | object;

export const RPATool = makeAssistantToolUI<RPAArgs, RPAResult>({
  toolName: "rpa_tool",
  render: ({ args, result, status }) => {
    const action = args.action;
    const isLoading = status.type === "running";
    
    let Icon = Monitor;
    if (action === "click" || action === "move") Icon = MousePointer;
    if (action === "type" || action === "press") Icon = Keyboard;
    
    return (
      <div className="my-2 rounded-lg border border-primary/20 bg-primary/5 overflow-hidden">
        <div className="flex items-center gap-2 bg-primary/10 px-3 py-2 border-b border-primary/20">
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin text-primary" />
          ) : (
            <Icon className="w-4 h-4 text-primary" />
          )}
          <span className="text-xs font-mono font-medium text-primary">RPA ACTION: {action?.toUpperCase()}</span>
        </div>
        
        <div className="p-3 font-mono text-xs">
          <div className="grid grid-cols-2 gap-2 mb-2">
            {Object.entries(args).map(([key, value]) => (
              key !== 'action' && (
                <div key={key} className="flex flex-col">
                  <span className="text-muted-foreground uppercase text-[10px]">{key}</span>
                  <span className="text-foreground truncate">{String(value)}</span>
                </div>
              )
            ))}
          </div>
          
          {result !== undefined && (
            <div className="mt-3 pt-2 border-t border-primary/10">
              <div className="text-[10px] text-muted-foreground uppercase mb-1">Result</div>
              <div className="text-primary/80 whitespace-pre-wrap">
                {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  },
});
