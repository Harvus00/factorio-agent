# knowledge_base/crawler/base_crawler.py
from typing import Optional, Set, List, Dict
import aiohttp
import logging
import asyncio
import time
from bs4 import BeautifulSoup
from dataclasses import dataclass

@dataclass
class BaseCrawlConfig:
    """Base configuration for all crawlers"""
    base_url: str
    max_pages: int = 1000
    max_depth: int = 3
    rate_limit: float = 1.0

class BaseCrawler:
    """Base crawler with common functionality"""
    def __init__(self, config: BaseCrawlConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.last_request_time = 0
        self.visited_urls: Set[str] = set()
        self.current_depth: int = 0
        self.pages: List[Dict] = []

    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            headers = {
                'User-Agent': 'FactorioAgent/1.0 (Educational Project)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            self.session = aiohttp.ClientSession(headers=headers)

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def _respect_rate_limit(self):
        """Rate limiting"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.config.rate_limit:
            await asyncio.sleep(self.config.rate_limit - time_since_last_request)
        self.last_request_time = time.time()

    async def fetch_page(self, url: str) -> str:
        """Fetch page content"""
        await self._respect_rate_limit()
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    self.logger.error(f"Failed to fetch {url}: Status {response.status}")
                    return ""
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return ""

    def parse_html(self, html_content: str) -> BeautifulSoup:
        """Parse HTML content"""
        return BeautifulSoup(html_content, 'html.parser')

    async def crawl(self) -> List[Dict]:
        """Main crawl method to be implemented by subclasses"""
        raise NotImplementedError

    async def __aenter__(self):
        await self.init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()