from src.spiders.base_spider import BaseSpider
from src.items import OpendataBridgeItem
from typing import Optional, Generator, Any
import scrapy
from datetime import datetime, timezone

class KokubunjiSpider(BaseSpider):
    """
    Spider for Kokubunji City (Code: 13214).
    Extracts raw content for later enrichment.
    """
    name = 'kokubunji'
    allowed_domains = ['city.kokubunji.tokyo.jp']
    start_urls = ['https://www.city.kokubunji.tokyo.jp/']
    municipality_code = '13214'

    def parse(self, response: scrapy.http.Response) -> Generator[Any, None, None]:
        item = self.parse_item(response)
        if item:
            yield item

        for href in response.css('a::attr(href)').getall():
            if not href or href.strip().startswith(('javascript:', '#', 'mailto:', 'tel:')):
                continue
            yield response.follow(href, callback=self.parse)

    def parse_item(self, response: scrapy.http.Response) -> Optional[OpendataBridgeItem]:
        # Target div: <div id="voice">
        content_div = response.css('div#voice').get()

        if not content_div:
            return None

        # Just extract the raw HTML string (or cleaned text) for the LLM to process later
        # We store it in 'body' as the raw source for enrichment
        return self.create_item(
            title=response.css('title::text').get() or 'No Title',
            body=content_div, # Store raw HTML or text representation
            url=response.url
        )
