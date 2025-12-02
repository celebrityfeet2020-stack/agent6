"""Web Search Tool - DuckDuckGo Search"""
from typing import Optional, List, Dict
from langchain_core.tools import BaseTool
from pydantic import Field
import requests
from bs4 import BeautifulSoup


class WebSearchTool(BaseTool):
    """Tool for searching the web using DuckDuckGo"""
    
    name: str = "web_search"
    description: str = """Search the web for information using DuckDuckGo.
    Input should be a search query string.
    Returns a list of search results with titles, URLs, and snippets."""
    
    def _run(self, query: str) -> str:
        """Execute web search"""
        try:
            # Use DuckDuckGo HTML search
            url = "https://html.duckduckgo.com/html/"
            data = {"q": query}
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            
            response = requests.post(url, data=data, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            for result in soup.find_all('div', class_='result')[:10]:
                title_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet
                    })
            
            if not results:
                return f"No results found for query: {query}"
            
            # Format results
            output = f"Search results for '{query}':\n\n"
            for i, result in enumerate(results, 1):
                output += f"{i}. {result['title']}\n"
                output += f"   URL: {result['url']}\n"
                output += f"   {result['snippet']}\n\n"
            
            return output
            
        except Exception as e:
            return f"Error performing web search: {str(e)}"
    
    async def _arun(self, query: str) -> str:
        """Async version"""
        return self._run(query)
