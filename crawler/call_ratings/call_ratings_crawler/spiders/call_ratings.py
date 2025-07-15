import scrapy


class CallRatingsSpider(scrapy.Spider):
    name = "call_ratings"
    allowed_domains = ["www.korcham.net"]

    
    def start_requests(self):
        base_url = 'https://www.korcham.net/nCham/Service/EconBrief/appl/ProspectBoardList.asp'
        params = {
            'board_type': 1,
            'daybt': 'OldNow',
            'm_OldDate': 20140811,
            'm_NowDate': 20240811
        }

        for page_index in range(1, 166):
            params['pageno'] = page_index
            url = f"{base_url}?{'&'.join([f'{key}={value}' for key, value in params.items()])}"
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        for row in response.css('div.tablewrap tbody tr'):
            data = row.css('*::text').getall()
            yield {
                '날짜': data[0],
                '콜금리': data[1],
                'CD(91일)': data[2],
                '국고채(3년)': data[3],
                '국고채(5년)': data[4],
                '회사채(3년,AA-)': data[5]
            }
