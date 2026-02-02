import scrapy
from scrapy_playwright.page import PageMethod

class GenericSpider(scrapy.Spider):
    name = "generic"

    def __init__(self, urls, selectors, document_id=None, collection=None, *args, **kwargs):
        super(GenericSpider, self).__init__(*args, **kwargs)
        self.urls = urls
        self.selectors = selectors
        self.document_id = document_id
        self.collection = collection

    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "networkidle"),
                    ],
                }
            )

    def parse(self, response):
        # Extract headings - get all text from within heading elements
        heading_selector = self.selectors.get("headings", "h1, h2, h3")
        headings = []
        for element in response.css(heading_selector):
            text = ''.join(element.css('::text').getall()).strip()
            if text:
                headings.append(text)
        
        # Extract paragraphs - get all text from within paragraph elements
        para_selector = self.selectors.get("paragraphs", "p")
        paragraphs = []
        for element in response.css(para_selector):
            text = ''.join(element.css('::text').getall()).strip()
            if text:
                paragraphs.append(text)
        
        item = {
            "url": response.url,
            "headings": headings,
            "paragraphs": paragraphs,
            "collection": self.collection,
        }
        yield item
