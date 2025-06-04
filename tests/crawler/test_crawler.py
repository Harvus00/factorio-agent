# tests/crawler/test_crawler.py
import asyncio
import logging
import sys
from pathlib import Path

project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

from src.knowledge_base.crawler.factorio_wiki_crawler import FactorioWikiCrawler, WikiCrawlConfig

async def test_wiki_crawler(url: str):
    crawler = FactorioWikiCrawler(WikiCrawlConfig(max_pages=3, max_depth=1))
    await crawler.crawl(url)
    crawler.save_to_json('wiki_pages_test.json')

if __name__ == "__main__":
    # url = "https://wiki.factorio.com/Pipe_to_ground"
    url="https://wiki.factorio.com/Pipe_to_ground"
    asyncio.run(test_wiki_crawler(url))