import { makeAssistantToolUI } from "@assistant-ui/react";
import { Globe, Loader2 } from "lucide-react";

type WebSearchArgs = {
  query: string;
};

type WebSearchResult = string;

export const WebSearchTool = makeAssistantToolUI<WebSearchArgs, WebSearchResult>({
  toolName: "web_search",
  render: ({ args, result, status }) => {
    const query = args.query;
    const isLoading = status.type === "running";
    
    return (
      <div className="my-2 rounded-lg border border-border/50 bg-card/50 overflow-hidden">
        <div className="flex items-center gap-2 bg-muted/30 px-3 py-2 border-b border-border/50">
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin text-primary" />
          ) : (
            <Globe className="w-4 h-4 text-primary" />
          )}
          <span className="text-xs font-mono font-medium text-muted-foreground">WEB SEARCH</span>
        </div>
        
        <div className="p-3">
          <div className="text-sm font-medium mb-2">Query: <span className="text-primary">{query}</span></div>
          
          {result !== undefined && (
            <div className="space-y-2 mt-3">
              <div className="text-xs text-muted-foreground font-mono uppercase">Results</div>
              <div className="text-sm text-foreground/80 line-clamp-4 whitespace-pre-wrap font-mono text-xs bg-muted/20 p-2 rounded">
                {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  },
});
