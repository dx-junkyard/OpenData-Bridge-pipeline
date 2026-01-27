from src.spiders.base_spider import BaseSpider
from src.items import OpendataBridgeItem
from src.utils import LLMHtmlConverter
from typing import Optional, Generator, Any
import scrapy
import os
from datetime import datetime, timezone

class KokubunjiSpider(BaseSpider):
    """
    Spider for Kokubunji City (Code: 13214).
    Uses LLM to parse HTML content into structured JSON.
    """
    name = 'kokubunji'
    allowed_domains = ['city.kokubunji.tokyo.jp']
    start_urls = ['https://www.city.kokubunji.tokyo.jp/']
    municipality_code = '13214'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm_url = os.getenv('OPENAI_BASE_URL')
        self.llm_api_key = os.getenv('OPENAI_API_KEY')
        self.llm_model = os.getenv('LLM_MODEL', 'gpt-4-turbo-preview')

        # Load prompt
        prompt_path = os.path.join(os.path.dirname(__file__), 'kokubunji_prompt.txt')
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.llm_prompt = f.read()
        except Exception as e:
            self.logger.error(f"Failed to load prompt file: {e}")
            self.llm_prompt = ""

        self.llm_converter = LLMHtmlConverter(
            llm_url=self.llm_url,
            llm_api_key=self.llm_api_key,
            llm_model=self.llm_model,
            llm_prompt=self.llm_prompt
        )

    def parse(self, response: scrapy.http.Response) -> Generator[Any, None, None]:
        """
        Override parse to handle 1-to-many item generation using LLM.
        """
        # Try to extract items from this page
        # In this spider, parse_item returns a list of items (generator)
        items = self.parse_item(response)
        if items:
            yield from items

        # Follow links
        for href in response.css('a::attr(href)').getall():
            if not href or href.strip().startswith(('javascript:', '#', 'mailto:', 'tel:')):
                continue
            yield response.follow(href, callback=self.parse)

    def parse_item(self, response: scrapy.http.Response) -> Generator[OpendataBridgeItem, None, None]:
        # Target div: <div id="voice">
        content_div = response.css('div#voice').get()

        if not content_div:
            return

        # Use LLM to convert HTML to JSON
        # This is a blocking call, which is not ideal for high-performance Scrapy,
        # but matches the requirement to reproduce the logic.
        structured_data_list = self.llm_converter.convert_html_to_json(content_div)

        if structured_data_list:
            for data in structured_data_list:
                item = OpendataBridgeItem(
                    title=data.get('タイトル', 'No Title'),
                    body=data.get('サービス内容', ''),
                    url=response.url,
                    municipality_code=self.municipality_code,
                    crawled_at=datetime.now(timezone.utc).isoformat(),
                    extended_attributes=data
                )
                yield item
        else:
            # Fallback or just skip if LLM fails or returns nothing
            # self.logger.warning(f"LLM returned no data for {response.url}")
            pass
