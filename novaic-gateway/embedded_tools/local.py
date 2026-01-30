"""
Local Tools - Host-side Web Search and Fetch

These tools run on the host machine for web operations.
"""

import os
import re
import httpx
from typing import Optional, Dict, Any

# API Keys
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")


async def web_search(
    query: str,
    count: Optional[int] = 10,
    freshness: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search the web using Brave Search API.
    
    Args:
        query: Search query string
        count: Number of results to return (default: 10, max: 20)
        freshness: Filter by freshness - 'pd' (past day), 'pw' (past week), 
                   'pm' (past month), 'py' (past year), or None for any time
    
    Returns:
        Dictionary with:
        - results: List of search results, each containing:
          - title: Page title
          - url: Page URL
          - description: Snippet/description
          - age: How old the result is (if available)
        - query: The search query used
        - total_count: Approximate total results
    """
    if not BRAVE_API_KEY:
        return {
            "error": "BRAVE_API_KEY not configured. Please set the environment variable.",
            "results": []
        }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "q": query,
                "count": min(count, 20),
            }
            if freshness:
                params["freshness"] = freshness
            
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params=params,
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": BRAVE_API_KEY
                }
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            web_results = data.get("web", {}).get("results", [])
            for item in web_results:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", ""),
                    "age": item.get("age", "")
                })
            
            return {
                "results": results,
                "query": query,
                "total_count": data.get("web", {}).get("total", len(results))
            }
    except httpx.HTTPError as e:
        return {"error": str(e), "results": []}


async def web_fetch(
    url: str,
    extract_main_content: Optional[bool] = True,
    max_length: Optional[int] = 50000
) -> Dict[str, Any]:
    """
    Fetch a web page and convert it to readable markdown.
    
    Args:
        url: URL of the web page to fetch
        extract_main_content: If True, extract only the main content (default: True)
        max_length: Maximum length of returned content in characters (default: 50000)
    
    Returns:
        Dictionary with:
        - url: The fetched URL
        - title: Page title
        - content: Page content in markdown format
        - word_count: Approximate word count
        - success: Whether the fetch was successful
    """
    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            html_content = response.text
            
            title = ""
            content = ""
            
            if extract_main_content:
                try:
                    from readability import Document
                    doc = Document(html_content)
                    title = doc.title()
                    html_content = doc.summary()
                except Exception:
                    pass
            
            # Convert HTML to markdown
            try:
                import html2text
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = False
                h.ignore_emphasis = False
                h.body_width = 0
                content = h.handle(html_content)
            except Exception:
                # Fallback: basic HTML tag removal
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, "html.parser")
                if not title:
                    title_tag = soup.find("title")
                    title = title_tag.get_text() if title_tag else ""
                content = soup.get_text(separator="\n", strip=True)
            
            # Extract title if not already done
            if not title:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                title_tag = soup.find("title")
                title = title_tag.get_text() if title_tag else url
            
            # Clean up content
            content = re.sub(r'\n{3,}', '\n\n', content)
            content = content.strip()
            
            # Truncate if too long
            if len(content) > max_length:
                content = content[:max_length] + "\n\n... [Content truncated]"
            
            word_count = len(content.split())
            
            return {
                "url": url,
                "title": title,
                "content": content,
                "word_count": word_count,
                "success": True
            }
    except httpx.HTTPError as e:
        return {
            "url": url,
            "error": str(e),
            "success": False
        }
    except Exception as e:
        return {
            "url": url,
            "error": f"Failed to parse content: {str(e)}",
            "success": False
        }
