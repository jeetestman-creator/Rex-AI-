"""
REX Web Scraping Skill
"""
import asyncio
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

from loguru import logger

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
except ImportError:
    webdriver = None

from skills.base_skill import BaseSkill


class WebScrapingSkill(BaseSkill):
    """Advanced Web Scraping Skill"""
    
    def __init__(self):
        super().__init__(
            name="web_scraping",
            description="Scrape and extract information from websites",
            version="1.0.0",
            category="web"
        )
    
    async def execute(self, user_input: str, decision: Dict, context: Dict) -> Dict:
        """Execute web scraping"""
        try:
            # Extract URL or search query from input
            url = self._extract_url(user_input)
            query = self._extract_search_query(user_input)
            
            if url:
                result = await self.scrape_url(url)
            elif query:
                result = await self.search_and_scrape(query)
            else:
                result = {"error": "No URL or search query found"}
            
            return {
                "text": self._format_result(result),
                "actions": ["display_results"],
                "data": result,
            }
        except Exception as e:
            return {
                "text": f"Scraping error: {str(e)}",
                "actions": [],
                "data": {"error": str(e)},
            }
    
    def _extract_url(self, text: str) -> Optional[str]:
        """Extract URL from text"""
        import re
        url_pattern = r'https?://[^\s]+|www\.[^\s]+'
        match = re.search(url_pattern, text)
        return match.group(0) if match else None
    
    def _extract_search_query(self, text: str) -> Optional[str]:
        """Extract search query from text"""
        patterns = [
            r'(?:search|find|look up|scrape)\s+(?:for\s+)?(.+)',
            r'(?:what|who|where)\s+(?:is|are)\s+(.+)',
        ]
        import re
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    async def scrape_url(self, url: str) -> Dict:
        """Scrape a specific URL"""
        if not requests or not BeautifulSoup:
            return {"error": "Required libraries not installed"}
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) REX-Bot/1.0'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract key information
            result = {
                "url": url,
                "title": soup.title.string if soup.title else "N/A",
                "headings": [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3'])[:10]],
                "paragraphs": [p.get_text(strip=True) for p in soup.find_all('p')[:5]],
                "links": [
                    {"text": a.get_text(strip=True), "url": urljoin(url, a.get('href', ''))}
                    for a in soup.find_all('a', href=True)[:10]
                ],
                "images": [
                    {"alt": img.get('alt', ''), "url": urljoin(url, img.get('src', ''))}
                    for img in soup.find_all('img')[:5]
                ],
                "meta_description": "",
            }
            
            # Get meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                result["meta_description"] = meta_desc.get('content', '')
            
            # Get main text content
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
                result["summary"] = text[:500] + "..." if len(text) > 500 else text
            
            return result
            
        except Exception as e:
            return {"error": f"Scraping failed: {str(e)}"}
    
    async def search_and_scrape(self, query: str) -> Dict:
        """Search and scrape top results"""
        if not requests or not BeautifulSoup:
            return {"error": "Required libraries not installed"}
        
        try:
            # Use DuckDuckGo (no API key needed)
            search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) REX-Bot/1.0'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            for result in soup.find_all('div', class_='result')[:5]:
                title_elem = result.find('a', class_='result__snippet')
                link_elem = result.find('a', class_='result__url')
                
                if title_elem:
                    results.append({
                        "title": title_elem.get_text(strip=True),
                        "url": link_elem.get_text(strip=True) if link_elem else "",
                    })
            
            return {
                "query": query,
                "results": results,
                "count": len(results),
            }
            
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    def _format_result(self, result: Dict) -> str:
        """Format scraping result for display"""
        if "error" in result:
            return f"❌ {result['error']}"
        
        parts = []
        
        if "title" in result:
            parts.append(f"📄 Title: {result['title']}")
        
        if "summary" in result:
            parts.append(f"\n📝 Summary:\n{result['summary']}")
        
        if "results" in result:
            parts.append(f"\n🔍 Search Results ({result['count']} found):")
            for i, r in enumerate(result['results'], 1):
                parts.append(f"  {i}. {r.get('title', 'N/A')}")
        
        return '\n'.join(parts) if parts else "No results found."
    
    async def scrape_with_selenium(self, url: str) -> Dict:
        """Scrape dynamic content using Selenium"""
        if not webdriver:
            return {"error": "Selenium not installed"}
        
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            
            # Wait for page load
            await asyncio.sleep(3)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            result = {
                "url": url,
                "title": driver.title,
                "content": soup.get_text(separator=' ', strip=True)[:1000],
            }
            
            driver.quit()
            return result
            
        except Exception as e:
            return {"error": f"Selenium scraping failed: {str(e)}"}


def register_skills(engine):
    """Register skill with REX engine"""
    skill = WebScrapingSkill()
    engine.register_skill(
        name="web_scraping",
        handler=skill.execute,
        description=skill.description
    )
