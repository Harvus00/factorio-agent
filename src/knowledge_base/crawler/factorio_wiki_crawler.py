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
                    'content': content
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
            r'/Main_Page',
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
            
        # Remove reference section and retrieved from text
        for element in content_div.find_all('div', class_="printfooter"):
            if element.get('id') == 'mw-references-wrap' or 'Retrieved from' in element.get_text():
                element.decompose()
        
        # Handle "See also", "Gallery", "History", and their subsequent content
        all_h2_headings = content_div.find_all('h2')
        sections_to_filter_out = ['See also', 'Gallery', 'History']
        
        for heading in all_h2_headings:
            heading_span = heading.find('span', class_='mw-headline')
            if heading_span and heading_span.get_text(strip=True) in sections_to_filter_out:
                # Find next heading
                next_heading = heading.find_next_sibling('h2')
                # If found next heading, remove everything between current heading and next heading
                if next_heading:
                    current = heading
                    while current and current != next_heading:
                        next_node = current.next_sibling
                        current.decompose()
                        current = next_node
                else:
                    # If no next heading, remove everything from current heading to end
                    current = heading
                    while current:
                        next_node = current.next_sibling
                        current.decompose()
                        current = next_node

        # Process all tables in the infobox
        infobox_output_parts = []
        for div in content_div.find_all('div', class_='infobox'):
            for table in div.find_all('table', recursive=False):
                if table.get('class') and 'hidden' in table.get('class'):
                    table.decompose()
                    continue
                # Process each row in the table
                for tr in table.find('tbody').find_all('tr', recursive=False):
                    row_parts = []
                    for cell in tr.find_all(['td', 'th']):
                        if 'Storage siz e' in cell.get_text(strip=True) or 'Health' in cell.get_text(strip=True) or 'Map color' in cell.get_text(strip=True) or 'Rocket capacity' in cell.get_text(strip=True):
                            cell.decompose()
                            break
                        # Replace all links with their titles
                        for link in cell.find_all('a'):
                            if link.get('title'):
                                link.replace_with(link.get('title').replace(' ', '_'))
                        # Get cell text
                        cell_text = cell.get_text(strip=True)
                        if cell_text:
                            cell_text = re.sub(r'(\d+)([a-zA-Z])', r'\1 \2', cell_text)
                            cell_text = re.sub(r'([a-zA-Z])(\d+)', r'\1 \2', cell_text)
                            cell_text = re.sub(r'([^ ])→', r'\1 →', cell_text)
                            cell_text = re.sub(r'→([^ ])', r'→ \1', cell_text)
                            row_parts.append(cell_text)
                    if row_parts:
                        infobox_output_parts.append(' '.join(row_parts))
                        infobox_output_parts.append(' | ')
                table.extract()  # Remove the table from the DOM after processing
            div.extract()
        main_body_text = content_div.get_text(separator='\n', strip=True)

        # Combine all parts with clear separation
        final_content = ''
        if infobox_output_parts:
            final_content += ''.join(infobox_output_parts) + '\n\n'
        final_content += main_body_text

        # Clean up excessive whitespace
        final_content = re.sub(r'\s+', ' ', final_content)
        final_content = re.sub(r'\n\s*\n', '\n', final_content)

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