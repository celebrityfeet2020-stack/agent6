import { ComposerPrimitive } from "@assistant-ui/react";
import { SendHorizontal, Square, Paperclip, FileText, Image as ImageIcon, Music, X } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import { useSoundEffects } from "@/hooks/useSoundEffects";

type FilePreview = {
  id: string;
  file: File;
  type: "image" | "audio" | "document";
  previewUrl?: string;
};

export const M3Composer = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<FilePreview[]>([]);
  const { playClick, playTyping, playSuccess } = useSoundEffects();

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const processFiles = (fileList: FileList) => {
    const newFiles: FilePreview[] = [];
    Array.from(fileList).forEach(file => {
      if (file.type.startsWith("video/")) {
        alert("暂不支持视频文件");
        return;
      }

      let type: FilePreview["type"] = "document";
      if (file.type.startsWith("image/")) type = "image";
      else if (file.type.startsWith("audio/")) type = "audio";

      newFiles.push({
        id: Math.random().toString(36).substr(2, 9),
        file,
        type,
        previewUrl: type === "image" ? URL.createObjectURL(file) : undefined
      });
    });
    setFiles(prev => [...prev, ...newFiles]);
    playSuccess();
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    processFiles(e.dataTransfer.files);
  }, []);

  const handlePaste = useCallback((e: React.ClipboardEvent) => {
    if (e.clipboardData.files.length > 0) {
      e.preventDefault();
      processFiles(e.clipboardData.files);
    }
  }, []);

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
    playClick();
  };

  return (
    <div 
      className={cn(
        "p-4 bg-background/95 backdrop-blur-sm border-t border-border/50 transition-colors duration-200 relative z-30",
        isDragging && "bg-primary/10 border-primary/50"
      )}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className="max-w-4xl mx-auto">
        {/* File Preview Bar */}
        {files.length > 0 && (
          <div className="flex gap-3 mb-3 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-primary/20">
            {files.map(file => (
              <div key={file.id} className="relative group shrink-0">
                <div className="w-16 h-16 rounded-lg border border-border bg-secondary/50 flex items-center justify-center overflow-hidden">
                  {file.type === "image" ? (
                    <img src={file.previewUrl} alt="preview" className="w-full h-full object-cover" />
                  ) : file.type === "audio" ? (
                    <Music className="w-8 h-8 text-muted-foreground" />
                  ) : (
                    <FileText className="w-8 h-8 text-muted-foreground" />
                  )}
                </div>
                <button 
                  onClick={() => removeFile(file.id)}
                  className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-destructive text-destructive-foreground flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-sm"
                >
                  <X className="w-3 h-3" />
                </button>
                <div className="text-[10px] text-muted-foreground truncate max-w-[64px] mt-1 text-center">
                  {file.file.name}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Drag Overlay Text */}
        {isDragging && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 backdrop-blur-sm z-50 rounded-t-xl border-t-2 border-primary border-dashed pointer-events-none">
            <div className="text-primary font-mono font-bold animate-pulse flex items-center gap-2">
              <Paperclip className="w-5 h-5" />
              释放以上传文件
            </div>
          </div>
        )}

        <ComposerPrimitive.Root className="flex flex-col gap-2">
          <div className="flex items-end gap-2 bg-secondary/50 border border-border rounded-xl p-2 focus-within:ring-1 focus-within:ring-primary/30 focus-within:border-primary/30 transition-all shadow-sm">
            <ComposerPrimitive.Input 
              placeholder="输入指令... (支持粘贴/拖拽文件)"
              className="flex-1 bg-transparent border-none focus:ring-0 resize-none max-h-32 min-h-[44px] py-2.5 px-3 text-sm font-mono placeholder:text-muted-foreground/50"
              onPaste={handlePaste}
              onKeyDown={() => {
                if (Math.random() > 0.7) playTyping();
              }}
            />
            <div className="flex gap-1 pb-1">
              <Tooltip>
                <TooltipTrigger asChild>
                  <button 
                    className="h-9 w-9 flex items-center justify-center rounded-lg text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
                    onClick={() => {
                      document.getElementById('file-upload')?.click();
                      playClick();
                    }}
                  >
                    <Paperclip className="w-4 h-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent>上传文件</TooltipContent>
              </Tooltip>
              <input 
                id="file-upload" 
                type="file" 
                multiple 
                className="hidden" 
                onChange={(e) => {
                  if (e.target.files) {
                    processFiles(e.target.files);
                  }
                }}
              />

              <div className="w-px h-6 bg-border/50 my-auto mx-1" />

              <ComposerPrimitive.Send asChild>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button 
                      className="h-9 w-9 flex items-center justify-center rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm"
                      onClick={playSuccess}
                    >
                      <SendHorizontal className="w-4 h-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>发送指令</TooltipContent>
                </Tooltip>
              </ComposerPrimitive.Send>
              <ComposerPrimitive.Cancel asChild>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button 
                      className="h-9 w-9 flex items-center justify-center rounded-lg bg-destructive text-destructive-foreground hover:bg-destructive/90 transition-colors shadow-sm"
                      onClick={playClick}
                    >
                      <Square className="w-4 h-4 fill-current" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>终止操作</TooltipContent>
                </Tooltip>
              </ComposerPrimitive.Cancel>
            </div>
          </div>
        </ComposerPrimitive.Root>
        
        <div className="mt-2 flex justify-center">
          <span className="text-[10px] font-mono text-muted-foreground/40 uppercase tracking-widest">
            M3 AGENT SYSTEM // 安全连接
          </span>
        </div>
      </div>
    </div>
  );
};
