import React, { useCallback, useEffect, useRef } from 'react';

interface ResizerProps {
  onResize: (delta: number) => void;
  direction?: 'horizontal' | 'vertical';
}

/**
 * 可拖动分割线组件
 * 
 * 功能:
 * - 支持水平/垂直方向拖动
 * - 鼠标悬停高亮
 * - 拖动时显示指示器
 */
export const Resizer: React.FC<ResizerProps> = ({
  onResize,
  direction = 'horizontal',
}) => {
  const isDragging = useRef(false);
  const startPos = useRef(0);
  
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    isDragging.current = true;
    startPos.current = direction === 'horizontal' ? e.clientY : e.clientX;
    document.body.style.cursor = direction === 'horizontal' ? 'row-resize' : 'col-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  }, [direction]);
  
  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging.current) return;
    
    const currentPos = direction === 'horizontal' ? e.clientY : e.clientX;
    const delta = currentPos - startPos.current;
    
    if (Math.abs(delta) > 5) { // 防止抖动
      onResize(delta);
      startPos.current = currentPos;
    }
  }, [direction, onResize]);
  
  const handleMouseUp = useCallback(() => {
    if (isDragging.current) {
      isDragging.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }
  }, []);
  
  useEffect(() => {
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);
  
  return (
    <div
      className={`resizer ${direction === 'horizontal' ? 'cursor-row-resize' : 'cursor-col-resize'}`}
      onMouseDown={handleMouseDown}
      role="separator"
      aria-orientation={direction}
      title="拖动调整大小"
    />
  );
};
