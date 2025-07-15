import scrapy


class InterestRatesSpider(scrapy.Spider):
    name = "interest_rates"
    allowed_domains = ["www.bok.or.kr"]

    def start_requests(self):
        base_url = 'https://www.bok.or.kr/portal/singl/baseRate/list.do'
        params = {
            'dataSeCd': '01',
            'menuNo': '200643'
        }
        url = f"{base_url}?{'&'.join([f'{key}={value}' for key, value in params.items()])}"
        yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        for row in response.css('div.table tbody tr'):
            data = row.css('td::text').getall()
            print(len(data))
            yield {
                '연도': data[0],
                '날짜': data[1],
                '기준금리': data[2]
            }
