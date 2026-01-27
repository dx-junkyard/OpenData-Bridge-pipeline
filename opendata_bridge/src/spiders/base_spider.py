import scrapy
from datetime import datetime, timezone
from src.items import OpendataBridgeItem
from typing import Optional, Generator, Any

class BaseSpider(scrapy.Spider):
    """
    Base Spider for Opendata Bridge project.
    Contains common logic for crawling and data extraction.
    """
    allowed_domains: list[str] = []
    start_urls: list[str] = []
    municipality_code: str = ""

    def parse(self, response: scrapy.http.Response) -> Generator[Any, None, None]:
        """
        Standard parse method.
        1. Parse the current page for items.
        2. Follow links to other pages within the allowed domain.
        """
        # Try to extract an item from this page
        item = self.parse_item(response)
        if item:
            yield item

        # Follow links
        # This is a basic crawler logic: follow all links in the same domain
        # Subclasses can override this or restrict the scope
        for href in response.css('a::attr(href)').getall():
            if not href or href.strip().startswith(('javascript:', '#', 'mailto:', 'tel:')):
                continue
            yield response.follow(href, callback=self.parse)

    def parse_item(self, response: scrapy.http.Response) -> Optional[OpendataBridgeItem]:
        """
        Abstract method to extract item from a page.
        Override this in child classes to implement specific extraction logic.
        """
        return None

    def clean_text(self, text: Optional[str]) -> str:
        """
        Utility to clean whitespace from text.
        """
        if not text:
            return ""
        return " ".join(text.split())

    def create_item(self, title: str, body: str, url: str) -> OpendataBridgeItem:
        """
        Helper to create an OpendataBridgeItem with common fields.
        """
        return OpendataBridgeItem(
            title=self.clean_text(title),
            body=self.clean_text(body),
            url=url,
            municipality_code=self.municipality_code,
            crawled_at=datetime.now(timezone.utc).isoformat()
        )
