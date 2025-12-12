import React, { lazy, Suspense } from 'react';
import { Loader } from 'lucide-react';

/**
 * Generative UI 组件注册表
 * 
 * Agent可以动态生成这些组件来增强用户体验
 */

// 懒加载组件
const SearchResultCard = lazy(() => import('./generative/SearchResultCard'));
const DataChart = lazy(() => import('./generative/DataChart'));
const WeatherCard = lazy(() => import('./generative/WeatherCard'));
const CodeBlock = lazy(() => import('./generative/CodeBlock'));
const ImageGallery = lazy(() => import('./generative/ImageGallery'));
const TaskList = lazy(() => import('./generative/TaskList'));

// 组件映射表
const COMPONENT_MAP: Record<string, React.LazyExoticComponent<any>> = {
  SearchResultCard,
  DataChart,
  WeatherCard,
  CodeBlock,
  ImageGallery,
  TaskList,
};

interface GenerativeComponentProps {
  component: string;
  props: Record<string, any>;
}

/**
 * Generative UI 组件容器
 * 
 * 根据component名称动态加载对应的React组件
 */
export const GenerativeComponent: React.FC<GenerativeComponentProps> = ({
  component,
  props,
}) => {
  const Component = COMPONENT_MAP[component];
  
  if (!Component) {
    console.warn(`Unknown generative component: ${component}`);
    return (
      <div className="generative-component-error">
        <p className="text-sm text-red-500">未知组件: {component}</p>
      </div>
    );
  }
  
  return (
    <Suspense
      fallback={
        <div className="generative-component-loading">
          <Loader className="w-5 h-5 animate-spin" />
          <span className="text-sm text-gray-500">加载组件...</span>
        </div>
      }
    >
      <Component {...props} />
    </Suspense>
  );
};

/**
 * 使用示例:
 * 
 * Agent在后端返回:
 * {
 *   type: "message",
 *   content: "这是搜索结果",
 *   component: "SearchResultCard",
 *   componentProps: {
 *     title: "Python教程",
 *     url: "https://...",
 *     snippet: "...",
 *     thumbnail: "..."
 *   }
 * }
 * 
 * 前端会自动渲染SearchResultCard组件
 */
