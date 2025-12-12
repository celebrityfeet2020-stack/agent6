import React, { useState, useRef, useCallback } from 'react';
import { Upload, X, File, Image, Video, Music, FileText } from 'lucide-react';

interface UploadedFile {
  id: string;
  file: File;
  preview?: string;
  type: 'image' | 'video' | 'audio' | 'text' | 'other';
}

interface FileUploadProps {
  onFilesChange: (files: File[]) => void;
  maxFiles?: number;
  acceptedTypes?: string[];
}

/**
 * 文件上传组件
 * 
 * 支持:
 * - 拖拽上传
 * - 点击上传
 * - 粘贴上传
 * - 多文件
 * - 预览 (图片/视频)
 * - 全格式支持 (音频/视频/图片/文本等)
 */
export const FileUpload: React.FC<FileUploadProps> = ({
  onFilesChange,
  maxFiles = 10,
  acceptedTypes = ['*/*'],
}) => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // 获取文件类型
  const getFileType = (file: File): UploadedFile['type'] => {
    if (file.type.startsWith('image/')) return 'image';
    if (file.type.startsWith('video/')) return 'video';
    if (file.type.startsWith('audio/')) return 'audio';
    if (file.type.startsWith('text/')) return 'text';
    return 'other';
  };
  
  // 获取文件图标
  const getFileIcon = (type: UploadedFile['type']) => {
    switch (type) {
      case 'image': return <Image className="w-5 h-5" />;
      case 'video': return <Video className="w-5 h-5" />;
      case 'audio': return <Music className="w-5 h-5" />;
      case 'text': return <FileText className="w-5 h-5" />;
      default: return <File className="w-5 h-5" />;
    }
  };
  
  // 处理文件
  const handleFiles = useCallback(async (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    
    // 检查文件数量限制
    if (uploadedFiles.length + fileArray.length > maxFiles) {
      alert(`最多只能上传 ${maxFiles} 个文件`);
      return;
    }
    
    // 处理每个文件
    const newFiles: UploadedFile[] = await Promise.all(
      fileArray.map(async (file) => {
        const type = getFileType(file);
        let preview: string | undefined;
        
        // 为图片生成预览
        if (type === 'image') {
          preview = await new Promise<string>((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target?.result as string);
            reader.readAsDataURL(file);
          });
        }
        
        return {
          id: `${Date.now()}-${Math.random()}`,
          file,
          preview,
          type,
        };
      })
    );
    
    const updated = [...uploadedFiles, ...newFiles];
    setUploadedFiles(updated);
    onFilesChange(updated.map(f => f.file));
  }, [uploadedFiles, maxFiles, onFilesChange]);
  
  // 拖拽处理
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);
  
  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);
  
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);
  
  // 点击上传
  const handleClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);
  
  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  }, [handleFiles]);
  
  // 粘贴上传
  const handlePaste = useCallback((e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    
    const files: File[] = [];
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.kind === 'file') {
        const file = item.getAsFile();
        if (file) files.push(file);
      }
    }
    
    if (files.length > 0) {
      handleFiles(files);
      e.preventDefault();
    }
  }, [handleFiles]);
  
  // 删除文件
  const handleRemove = useCallback((id: string) => {
    const updated = uploadedFiles.filter(f => f.id !== id);
    setUploadedFiles(updated);
    onFilesChange(updated.map(f => f.file));
  }, [uploadedFiles, onFilesChange]);
  
  return (
    <div className="space-y-2" onPaste={handlePaste}>
      {/* 上传区域 */}
      {uploadedFiles.length < maxFiles && (
        <div
          className={`file-upload-area ${isDragOver ? 'drag-over' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleClick}
        >
          <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
          <p className="text-sm text-gray-400">
            点击、拖拽或粘贴上传文件
          </p>
          <p className="text-xs text-gray-500 mt-1">
            支持图片、视频、音频、文本等全格式
          </p>
          
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept={acceptedTypes.join(',')}
            onChange={handleFileInputChange}
            className="hidden"
          />
        </div>
      )}
      
      {/* 文件列表 */}
      {uploadedFiles.length > 0 && (
        <div className="space-y-2">
          {uploadedFiles.map((uploadedFile) => (
            <div key={uploadedFile.id} className="file-preview">
              {/* 图标或预览 */}
              <div className="file-preview-icon">
                {uploadedFile.preview ? (
                  <img
                    src={uploadedFile.preview}
                    alt={uploadedFile.file.name}
                    className="w-10 h-10 object-cover rounded"
                  />
                ) : (
                  getFileIcon(uploadedFile.type)
                )}
              </div>
              
              {/* 文件信息 */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {uploadedFile.file.name}
                </p>
                <p className="text-xs text-gray-500">
                  {(uploadedFile.file.size / 1024).toFixed(1)} KB
                </p>
              </div>
              
              {/* 删除按钮 */}
              <button
                onClick={() => handleRemove(uploadedFile.id)}
                className="file-preview-remove"
                title="删除"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
