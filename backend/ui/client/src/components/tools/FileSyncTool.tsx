import { makeAssistantToolUI } from "@assistant-ui/react";
import { FileText, Upload, Download, Loader2 } from "lucide-react";

type FileSyncArgs = {
  operation: string;
  source_path: string;
  destination_path: string;
};

type FileSyncResult = string;

export const FileSyncTool = makeAssistantToolUI<FileSyncArgs, FileSyncResult>({
  toolName: "file_sync_tool",
  render: ({ args, result, status }) => {
    const operation = args.operation;
    const isLoading = status.type === "running";
    
    let Icon = FileText;
    if (operation === "push") Icon = Upload;
    if (operation === "pull") Icon = Download;
    
    return (
      <div className="my-2 rounded-lg border border-border/50 bg-card/50 overflow-hidden">
        <div className="flex items-center gap-2 bg-muted/30 px-3 py-2 border-b border-border/50">
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin text-primary" />
          ) : (
            <Icon className="w-4 h-4 text-primary" />
          )}
          <span className="text-xs font-mono font-medium text-muted-foreground">FILE SYNC: {operation?.toUpperCase()}</span>
        </div>
        
        <div className="p-3 font-mono text-xs">
          <div className="space-y-2">
            <div className="flex flex-col">
              <span className="text-muted-foreground uppercase text-[10px]">Source</span>
              <span className="text-foreground break-all">{String(args.source_path)}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-muted-foreground uppercase text-[10px]">Destination</span>
              <span className="text-foreground break-all">{String(args.destination_path)}</span>
            </div>
          </div>
          
          {result !== undefined && (
            <div className="mt-3 pt-2 border-t border-border/50">
              <div className="text-[10px] text-muted-foreground uppercase mb-1">Status</div>
              <div className="text-green-500">
                {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  },
});
