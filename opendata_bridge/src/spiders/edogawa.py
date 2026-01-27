from src.spiders.base_spider import BaseSpider
from src.items import OpendataBridgeItem
from typing import Optional
import scrapy

class EdogawaSpider(BaseSpider):
    """
    Spider for Edogawa City (Code: 13123).
    Migrated from custom pipeline logic.
    """
    name = 'edogawa'
    allowed_domains = ['city.edogawa.tokyo.jp']
    start_urls = ['https://www.city.edogawa.tokyo.jp/']
    municipality_code = '13123'

    # Logic extracted from pipeline configuration (pipeline.yaml / web_data2csv_step.py)
    # These keywords filter which pages are relevant for the catalog.
    include_keywords = [
        "児", "子育", "ファミリー", "保育", "離乳", "教育",
        "食育", "ベビー", "赤ちゃん", "妊", "出産", "産後"
    ]

    def parse_item(self, response: scrapy.http.Response) -> Optional[OpendataBridgeItem]:
        # Selector logic based on Edogawa site structure

        # Title: usually the h1
        title = response.css('h1::text').get()
        if not title:
            # If no H1, it might not be a content page
            return None

        # Body: Main content wrapper
        # Identified selector: <main id="tmp_wrap_main" class="column_cnt">
        # Improved: div.col_main seems to be the inner content column.
        body_node = response.css('div.col_main') or response.css('main#tmp_wrap_main')

        if not body_node:
            # If main content wrapper is missing, try generic fallback or skip
            # Often top pages or search pages might have different structure
            return None

        # Extract text from the body, joining with spaces
        body_text = " ".join(body_node.css('::text').getall())
        cleaned_body = self.clean_text(body_text)

        # Keyword filtering Logic
        # Translating the "include_keywords" logic from the old pipeline.
        # Only keep items that contain at least one of the keywords.
        if not any(k in cleaned_body for k in self.include_keywords):
            # self.logger.debug(f"Skipping {response.url} - no keywords match")
            return None

        return self.create_item(
            title=title,
            body=cleaned_body,
            url=response.url
        )
