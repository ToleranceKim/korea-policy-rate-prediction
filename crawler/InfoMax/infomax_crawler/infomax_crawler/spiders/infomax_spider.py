import scrapy


class InfomaxSpiderSpider(scrapy.Spider):
    name = "infomax_spider"
    allowed_domains = ["einfomax.co.kr"]
    start_urls = ["https://einfomax.co.kr"]

    def parse(self, response):
        pass
