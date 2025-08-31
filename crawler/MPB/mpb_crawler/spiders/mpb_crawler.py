import scrapy
import PyPDF2
from io import BytesIO
import os
import time
import re
import requests


class MpbCrawlerSpider(scrapy.Spider):
    name = "mpb_crawler"
    allowed_domains = ["www.bok.or.kr", "file-cdn.bok.or.kr"]

    def start_requests(self):
        base_url = 'https://www.bok.or.kr/portal/singl/newsData/listCont.do'
        params = {
            'targetDepth': 4,
            'menuNo': 200789,
            'syncMenuChekKey': 1,
            'depthSubMain': '',
            'subMainAt': '',
            'searchCnd': 1,
            'searchKwd': '',
            'depth2': 200038,
            'depth3': 201154,
            'depth4': 200789,
        }

        # 작년 사양대로 30페이지만 수집 (2014~2025년 약 200건)
        for page_index in range(1, 31):
            params['pageIndex'] = page_index
            url = f"{base_url}?{'&'.join([f'{key}={value}' for key, value in params.items()])}"
            yield scrapy.Request(url=url, callback=self.parse)
        

    def parse(self, response):
        # links for each articles in the list
        for news_item in response.css('li.bbsRowCls'):
            news_link = news_item.css('a.title::attr(href)').get()
            title_element = news_item.css('a.title')
            
            if news_link and title_element:
                title = ''.join(title_element.css('::text').getall()).strip()
                if title:
                    self.logger.info(f"Found article: {title}")
                    yield response.follow(news_link, self.download_pdf, meta={'title': title})
                else:
                    self.logger.warning(f"Empty title for link: {news_link}")

    def download_pdf(self, response):
        base_url = 'https://www.bok.or.kr'
        pdf_links = response.css('a.file::attr(href)').getall()
        title = response.meta.get('title')

        if len(pdf_links) > 1:
            pdf_link = pdf_links[0] if 'pdf' in pdf_links[0] else pdf_links[1]
            pdf_url = base_url + pdf_link
            yield scrapy.Request(pdf_url, callback=self.parse_pdf, meta={'title': title})

    def parse_pdf(self, response):
        try:
            # PyPDF2로 PDF 텍스트 추출
            pdf_file = BytesIO(response.body)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            # 제목에서 날짜 추출
            date_matches = re.findall(r'(\d{4}\.\d{1,2}\.\d{1,2})', response.meta['title'])
            date = date_matches[0] if date_matches else None
            title = response.meta['title']

            # section2 (위원 토의내용) 추출
            discussion_pattern = r"위원 토의내용(.*?)심의결과"
            discussion_content = re.search(discussion_pattern, text, re.DOTALL)
            discussion_text = discussion_content.group(1).strip().replace('\n', '') if discussion_content else None

            # section3 (심의결과) 추출
            decision_pattern = r"심의결과(.*)"
            decision_content = re.search(decision_pattern, text, re.DOTALL)
            decision_text = decision_content.group(1).strip().replace('\n', '') if decision_content else None

            if text.strip():
                yield {
                    'date': date,
                    'title': title,
                    'content': text,
                    'discussion': discussion_text,
                    'decision': decision_text,
                    'link': response.url
                }
                self.logger.info(f"Successfully processed PDF: {title}")
            else:
                self.logger.warning(f"Empty PDF content for: {title}")
    
        except Exception as e:
            self.logger.error(f"Error parsing PDF {response.url}: {e}")
            # Fallback: 빈 컨텐츠로라도 메타데이터 수집
            yield {
                'date': None,
                'title': response.meta.get('title', 'Unknown'),
                'content': None,
                'discussion': None,
                'decision': None,
                'link': response.url,
                'error': str(e)
            }