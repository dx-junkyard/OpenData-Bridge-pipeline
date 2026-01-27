import scrapy

class OpendataBridgeItem(scrapy.Item):
    """
    Item definition for Opendata Bridge.

    Attributes:
        title (str): The title of the page/service.
        body (str): The main content of the page.
        url (str): The source URL.
        municipality_code (str): The 6-digit code of the municipality.
        crawled_at (str): ISO formatted timestamp of crawl time.
    """
    title = scrapy.Field()
    body = scrapy.Field()
    url = scrapy.Field()
    municipality_code = scrapy.Field()
    crawled_at = scrapy.Field()
