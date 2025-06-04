# scripts/crawl.py
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from knowledge_base.crawler.factorio_wiki_crawler import FactorioWikiCrawler, WikiCrawlConfig

async def crawl_all():
    # create data directory
    data_dir = Path("data")
    raw_dir = data_dir / "raw"
    
    for dir_path in [raw_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # crawl wiki
    wiki_config = WikiCrawlConfig(max_pages=300)
    async with FactorioWikiCrawler(wiki_config) as crawler:
        pages = await crawler.crawl()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        crawler.save_to_json(raw_dir / f"wiki_pages_{timestamp}.json")
        print(f"Crawled {len(pages)} wiki pages")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(crawl_all())