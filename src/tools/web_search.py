"""
Web search tool — поиск в интернете через DuckDuckGo Lite.
Работает без API ключей, использует HTML scraping.
"""

import urllib.request
import urllib.parse
import re
from typing import Any, Dict

from .base import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    """Поиск в интернете через DuckDuckGo."""

    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for current information, documentation, best practices, or solutions. Returns search results with titles, URLs, and snippets. Use this when you need up-to-date information.",
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query. Be specific. Examples: 'python asyncio best practices 2024', 'docker compose healthcheck example'",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of results to return (1-10, default: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    async def execute(self, query: str, limit: int = 5, **kwargs) -> ToolResult:
        """Выполнить поиск через DuckDuckGo Lite."""
        try:
            limit = max(1, min(limit, 10))
            
            # DuckDuckGo Lite HTML endpoint
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://lite.duckduckgo.com/lite/?q={encoded_query}"
            
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0",
                },
            )
            
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode("utf-8", errors="replace")
            
            # Parse results from DuckDuckGo Lite HTML
            results = self._parse_ddg_lite(html, limit)
            
            if not results:
                return ToolResult(
                    success=True,
                    content="No search results found. Try a different query.",
                    metadata={"query": query, "results": 0},
                )
            
            lines = []
            for i, r in enumerate(results, 1):
                lines.append(f"{i}. {r['title']}")
                lines.append(f"   URL: {r['url']}")
                if r.get("snippet"):
                    snippet = r["snippet"][:300]
                    lines.append(f"   {snippet}")
                lines.append("")
            
            output = "\n".join(lines)
            return ToolResult(
                success=True,
                content=output,
                metadata={"query": query, "results": len(results)},
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=f"Web search failed: {str(e)}. Try again later or use a more specific query.",
            )
    
    def _parse_ddg_lite(self, html: str, limit: int) -> list:
        """Parse DuckDuckGo Lite HTML results."""
        results = []
        
        # DDG Lite uses specific HTML structure
        # Result rows have class .result-link or similar patterns
        # Simple regex-based parsing for robustness
        
        # Find all result blocks
        # Pattern: <a class="result-link" href="...">title</a>
        # Followed by: <td class="result-snippet">snippet</td>
        
        # Split by result rows
        parts = html.split('<tr>')
        
        for part in parts:
            # Extract link
            link_match = re.search(r'<a[^>]+class="result-link"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', part, re.DOTALL | re.IGNORECASE)
            if not link_match:
                link_match = re.search(r'<a[^>]+href="(/l/\?[^"]+)"[^>]*>(.*?)</a>', part, re.DOTALL | re.IGNORECASE)
            
            if link_match:
                href = link_match.group(1)
                title = re.sub(r'<[^>]+>', '', link_match.group(2)).strip()
                
                # Resolve redirect URLs
                if href.startswith('/l/?'):
                    href = 'https://lite.duckduckgo.com' + href
                elif href.startswith('/'):
                    href = 'https://lite.duckduckgo.com' + href
                
                # Extract snippet
                snippet = ""
                snippet_match = re.search(r'<td[^>]+class="result-snippet"[^>]*>(.*?)</td>', part, re.DOTALL | re.IGNORECASE)
                if snippet_match:
                    snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()
                
                results.append({
                    "title": title,
                    "url": href,
                    "snippet": snippet,
                })
                
                if len(results) >= limit:
                    break
        
        return results
