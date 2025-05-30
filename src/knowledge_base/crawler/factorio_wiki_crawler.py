# knowledge_base/crawler/factorio_wiki_crawler.py
from knowledge_base.crawler.base_crawler import BaseCrawler
from typing import List, Dict
import re
import json
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from typing import Optional
from dataclasses import dataclass
from .base_crawler import BaseCrawlConfig, BaseCrawler

@dataclass
class WikiCrawlConfig(BaseCrawlConfig):
    """Configuration for wiki crawler"""
    target_language: str = "en"
    max_depth: int = 1
    base_url: str = "https://wiki.factorio.com"
    rate_limit: float = 0.1

class FactorioWikiCrawler(BaseCrawler):
    def __init__(self, config: WikiCrawlConfig = None):
        super().__init__(config or WikiCrawlConfig())
        
    async def crawl(self, start_url: str = "https://wiki.factorio.com/Materials_and_recipes") -> List[Dict]:
        """Crawl wiki pages"""
        await self.init_session()
        try:
            await self._crawl_page(start_url)
            return self.pages
        finally:
            await self.close_session()

    async def _crawl_page(self, url: str):
        """Crawl a single wiki page"""
        if (url in self.visited_urls or 
            self.current_depth > self.config.max_depth or 
            len(self.pages) >= self.config.max_pages):
            return

        self.visited_urls.add(url)
        self.logger.info(f"Crawling: {url} at depth {self.current_depth}")

        html_content = await self.fetch_page(url)
        if not html_content:
            return

        soup = self.parse_html(html_content)
        
        # Check for 'Space Age' feature immediately after parsing, before any content extraction
        if self._has_space_age_feature_at_top(soup):
            self.logger.info(f"Skipping {url} due to 'Space Age expansion exclusive feature' at the top.")
            return

        if self._is_target_page(url):
            content = self._extract_page_content(soup)
            if content:
                self.pages.append({
                    'url': url,
                    'title': self._extract_title(soup),
                    'content': content,
                    'type': 'wiki'
                })

        # Find and crawl links
        links = self._extract_links(soup)
        for link in links:
            # We still want to crawl links on Space Age pages to discover other pages,
            # but we won't *store* the content of the Space Age page itself if it's filtered.
            if self._should_crawl_link(link):
                self.current_depth += 1
                await self._crawl_page(link)
                self.current_depth -= 1

    def _has_space_age_feature_at_top(self, soup: BeautifulSoup) -> bool:
        """
        Check if the page immediately states 'Space Age expansion exclusive feature'
        at the beginning of the main content.
        """
        content_div = soup.find('div', {'id': 'mw-content-text'})
        if content_div:
            # Look for the immediate <p> tag with the Space Age indicator
            first_p = content_div.find('p', recursive=False)
            if first_p and "Space Age expansion exclusive feature" in first_p.get_text():
                return True
            # Also check the infobox header for the Space Age icon
            infobox_header_icon_div = soup.find('div', class_='infobox-header').find('div', class_='factorio-icon-space-age') if soup.find('div', class_='infobox-header') else None
            if infobox_header_icon_div:
                return True
        return False

    def _is_target_page(self, url: str) -> bool:
        """
        Check if the page is a target page (English language and not a special page).
        """
        # This regex ensures we only match /en, /en-us etc.
        match = re.search(r'/([a-z]{2}(?:-[a-z]{2})?)$', url)
        if match:
            page_language = match.group(1) if match.group(1) else 'en'
            if page_language != self.config.target_language:
                return False
        
        # If the URL doesn't end with a language code, default to English, e.g., /Pipe_to_ground
        if not url.startswith(self.config.base_url):
            return False

        # Skip special pages and fragments
        skip_patterns = [
            r'/Space_Age',
            r'/Factorio:',
            r'/Special:',
            r'/Talk:',
            r'/User:',
            r'/File:',
            r'/Template:',
            r'/Help:',
            r'/Category:',
            r'/Module:',
            r'#', # Exclude anchor links within the same page
            r'\?', # Exclude URLs with query parameters
        ]

        for pattern in skip_patterns:
            if re.search(pattern, url):
                return False
        return True
    
    def _extract_link_text(self, element) -> str:
        """
        Extract text from an element, including the text of any links.
        Returns a tuple of (text, link_url) if the element is a link.
        """
        if not element:
            return ""
        
        if element.name == 'a':
            # use link text if available, otherwise use title attribute
            link_text = element.get_text(strip=True)
            if not link_text and element.get('title'):
                link_text = element.get('title').replace('_', ' ')
            return link_text
        return element.get_text(strip=True)

    def _extract_page_content(self, soup) -> str:
        """
        Extract main content from wiki page, applying the specified filtering.
        """
        content_div = soup.find('div', {'id': 'mw-content-text'})
        if not content_div:
            return ""

        # Remove unwanted elements immediately
        for element in content_div.find_all(['script', 'style', 'sup']):
            element.decompose()
        
        # Handle "See also", "Gallery", "History", and their subsequent content
        sections_to_filter_out = ['See also', 'Gallery', 'History']
        elements_to_remove = []
        for heading in content_div.find_all('h2'):
            heading_span = heading.find('span', class_='mw-headline')
            if heading_span and heading_span.get_text(strip=True) in sections_to_filter_out:
                elements_to_remove.append(heading)
                current_node = heading.next_sibling
                while current_node:
                    if isinstance(current_node, Tag) and current_node.name == 'h2':
                        break # Stop at the next h2
                    elements_to_remove.append(current_node)
                    current_node = current_node.next_sibling
        for element in elements_to_remove:
            element.decompose()
        
        # Handle inline "Space Age expansion exclusive feature" declarations
        for i_tag in content_div.find_all('i'):
            space_age_link = i_tag.find('a', href="/Space_Age", title="Space Age")
            if space_age_link and "Space Age expansion exclusive feature" in i_tag.get_text():
                i_tag.decompose()
        
        infobox_output_parts = []
        infobox_table = content_div.find('table')
        if infobox_table:
            # process all cells with icon
            for tr in infobox_table.find_all('tr'):
                recipe_cell = tr.find('td', class_='infobox-vrow-value')
                if recipe_cell:
                    recipe_parts = []
                    # split input and output
                    parts = str(recipe_cell).split('→')
                    if len(parts) == 2:
                        # process input part
                        input_parts = []
                        for icon_div in BeautifulSoup(parts[0], 'html.parser').find_all('div', class_='factorio-icon'):
                            item_link = icon_div.find('a')
                            quantity_div = icon_div.find('div', class_='factorio-icon-text')
                            if item_link and quantity_div:
                                item_name = item_link.get('title', '').replace('_', ' ')
                                quantity = quantity_div.get_text(strip=True)
                                input_parts.append(f"{quantity} {item_name}")
                        
                        # process output part
                        output_parts = []
                        for icon_div in BeautifulSoup(parts[1], 'html.parser').find_all('div', class_='factorio-icon'):
                            item_link = icon_div.find('a')
                            quantity_div = icon_div.find('div', class_='factorio-icon-text')
                            if item_link and quantity_div:
                                item_name = item_link.get('title', '').replace('_', ' ')
                                quantity = quantity_div.get_text(strip=True)
                                output_parts.append(f"{quantity} {item_name}")
                        
                        if input_parts and output_parts:
                            infobox_output_parts.append(f"{' + '.join(input_parts)} → {' + '.join(output_parts)}")
                    else:
                        # process cells without arrow
                        for icon_div in recipe_cell.find_all('div', class_='factorio-icon'):
                            item_link = icon_div.find('a')
                            quantity_div = icon_div.find('div', class_='factorio-icon-text')
                            if item_link and quantity_div:
                                item_name = item_link.get('title', '').replace('_', ' ')
                                quantity = quantity_div.get_text(strip=True)
                                recipe_parts.append(f"{quantity} {item_name}")
                        if recipe_parts:
                            infobox_output_parts.append(' + '.join(recipe_parts))
            
            # process other information rows
            for tr in infobox_table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) == 2:
                    key_p = tds[0].find('p')
                    value_p = tds[1].find('p')
                    if key_p and value_p:
                        key_text = key_p.get_text(strip=True)
                        value_text = value_p.get_text(strip=True)
                        if key_text and value_text:
                            infobox_output_parts.append(f"{key_text}: {value_text}")
            
            infobox_table.extract()

        main_body_text = content_div.get_text(separator=' ', strip=True)
        
        final_content = ' '.join(infobox_output_parts + [main_body_text])
        
        final_content = re.sub(r'\s+', ' ', final_content)
        
        return final_content.strip()
    
    def _extract_title(self, soup) -> str:
        """
        Extract page title
        """
        title_elem = soup.find('h1', {'id': 'firstHeading'})
        return title_elem.get_text(strip=True) if title_elem else ""
    
    def _extract_links(self, soup) -> List[str]:
        """
        Extract all wiki links from the page
        """
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # Only consider internal wiki links that are not special pages or anchors
            if href.startswith('/'):
                full_url = urljoin(self.config.base_url, href)
                # Ensure the link is not an internal anchor on the same page
                if '#' not in href:
                    links.append(full_url)
        return links

    def _should_crawl_link(self, url: str) -> bool:
        """
        Determine if a link should be crawled based on various criteria.
        """
        # check if it's a target language page
        if not self._is_target_page(url):
            return False
            
        # check if it's already visited
        if url in self.visited_urls:
            return False
            
        # check if it's already reached the max pages
        if len(self.pages) >= self.config.max_pages:
            return False
            
        # check if it's already reached the max depth
        if self.current_depth >= self.config.max_depth:
            return False
        return True

    def save_to_json(self, filename: str):
        """
        Save crawled data to JSON file
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.pages, f, ensure_ascii=False, indent=2)