import React from 'react';
import { ExternalLink } from 'lucide-react';

interface SearchResultCardProps {
  title: string;
  url: string;
  snippet: string;
  thumbnail?: string;
}

/**
 * 搜索结果卡片 (Generative UI示例)
 * 
 * Agent可以在搜索后动态生成这个组件来展示结果
 */
const SearchResultCard: React.FC<SearchResultCardProps> = ({
  title,
  url,
  snippet,
  thumbnail,
}) => {
  return (
    <div className="search-result-card">
      {thumbnail && (
        <div className="search-result-thumbnail">
          <img src={thumbnail} alt={title} />
        </div>
      )}
      
      <div className="search-result-content">
        <h3 className="search-result-title">
          <a href={url} target="_blank" rel="noopener noreferrer">
            {title}
            <ExternalLink className="w-4 h-4 ml-1 inline" />
          </a>
        </h3>
        
        <p className="search-result-snippet">{snippet}</p>
        
        <div className="search-result-url">
          <span className="text-xs text-gray-500">{url}</span>
        </div>
      </div>
    </div>
  );
};

export default SearchResultCard;
