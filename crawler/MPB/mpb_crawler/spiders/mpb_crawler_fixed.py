import scrapy
import PyPDF2
from io import BytesIO
import re
from datetime import datetime


class MpbCrawlerFixedSpider(scrapy.Spider):
    """개선된 MPB 의사록 크롤러 - 동적 페이지네이션 및 기간 설정"""
    name = "mpb_crawler_fixed"
    allowed_domains = ["www.bok.or.kr", "file-cdn.bok.or.kr"]
    
    def __init__(self, start_year=2014, end_year=2025, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_year = int(start_year)
        self.end_year = int(end_year)
        self.page_count = 0
        self.total_items = 0
        self.collected_items = []
        
    def start_requests(self):
        """첫 페이지 요청으로 전체 페이지 수 파악"""
        base_url = 'https://www.bok.or.kr/portal/singl/newsData/listCont.do'
        params = {
            'targetDepth': 4,
            'menuNo': 200789,
            'syncMenuChekKey': 1,
            'searchCnd': 1,
            'searchKwd': '',
            'depth2': 200038,
            'depth3': 201154,
            'depth4': 200789,
            'pageIndex': 1
        }
        
        url = f"{base_url}?{'&'.join([f'{key}={value}' for key, value in params.items()])}"
        yield scrapy.Request(url=url, callback=self.parse_first_page, meta={'params': params})
    
    def parse_first_page(self, response):
        """첫 페이지에서 전체 페이지 수 파악"""
        # 전체 페이지 수 추출
        pagination = response.css('div.paging')
        if pagination:
            # 마지막 페이지 번호 찾기
            last_page_link = pagination.css('a.last::attr(href)').get()
            if last_page_link:
                import re
                page_match = re.search(r'pageIndex["\']?\s*[:=]\s*(\d+)', last_page_link)
                if page_match:
                    total_pages = int(page_match.group(1))
                else:
                    # 페이지 번호들에서 최대값 찾기
                    page_numbers = pagination.css('a::text').re(r'\d+')
                    total_pages = max(map(int, page_numbers)) if page_numbers else 10
            else:
                # 페이지 번호 직접 추출
                page_numbers = pagination.css('a::text').re(r'\d+')
                total_pages = max(map(int, page_numbers)) if page_numbers else 10
        else:
            # 페이지네이션이 없으면 기본값
            total_pages = 10
            
        self.logger.info(f"전체 페이지 수: {total_pages}")
        
        # 첫 페이지 파싱
        yield from self.parse(response)
        
        # 나머지 페이지 요청
        base_url = 'https://www.bok.or.kr/portal/singl/newsData/listCont.do'
        params = response.meta['params']
        
        for page_index in range(2, total_pages + 1):
            params['pageIndex'] = page_index
            url = f"{base_url}?{'&'.join([f'{key}={value}' for key, value in params.items()])}"
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        """각 페이지의 회의록 목록 파싱"""
        for news_item in response.css('li.bbsRowCls'):
            # 제목과 날짜 추출
            title_element = news_item.css('a.title')
            if title_element:
                title = ''.join(title_element.css('::text').getall()).strip()
                
                # 날짜 추출 및 연도 필터링
                date_match = re.search(r'(\d{4})\.(\d{1,2})\.(\d{1,2})', title)
                if date_match:
                    year = int(date_match.group(1))
                    
                    # 지정된 기간 내의 회의록만 수집
                    if self.start_year <= year <= self.end_year:
                        news_link = news_item.css('a.title::attr(href)').get()
                        if news_link:
                            self.logger.info(f"수집 대상: {title} ({year}년)")
                            yield response.follow(news_link, self.download_pdf, meta={'title': title})
                    else:
                        self.logger.debug(f"기간 외: {title} ({year}년)")
                else:
                    self.logger.warning(f"날짜 추출 실패: {title}")
    
    def download_pdf(self, response):
        """PDF 링크 추출 및 다운로드"""
        base_url = 'https://www.bok.or.kr'
        pdf_links = response.css('a.file::attr(href)').getall()
        title = response.meta.get('title')
        
        # PDF 링크 찾기
        pdf_url = None
        for link in pdf_links:
            if 'pdf' in link.lower() or link.endswith('.pdf'):
                pdf_url = base_url + link if not link.startswith('http') else link
                break
        
        # 첫 번째 링크 사용 (PDF가 없으면)
        if not pdf_url and pdf_links:
            pdf_url = base_url + pdf_links[0] if not pdf_links[0].startswith('http') else pdf_links[0]
        
        if pdf_url:
            yield scrapy.Request(pdf_url, callback=self.parse_pdf, meta={'title': title})
        else:
            self.logger.warning(f"PDF 링크 없음: {title}")
    
    def parse_pdf(self, response):
        """PDF 파싱 및 데이터 추출"""
        try:
            # PyPDF2로 PDF 텍스트 추출
            pdf_file = BytesIO(response.body)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
                except Exception as e:
                    self.logger.warning(f"페이지 {page_num+1} 추출 실패: {e}")
            
            # 메타데이터 추출
            title = response.meta['title']
            date_match = re.search(r'(\d{4})\.(\d{1,2})\.(\d{1,2})', title)
            date = date_match.group(0) if date_match else None
            year = int(date_match.group(1)) if date_match else None
            
            # 섹션별 내용 추출
            discussion_text = None
            decision_text = None
            
            # 다양한 패턴 시도
            patterns = [
                (r"위원\s*토의\s*내용(.*?)심의\s*결과", r"심의\s*결과(.*)"),
                (r"토의\s*내용(.*?)심의\s*결과", r"심의\s*결과(.*)"),
                (r"위원\s*토의(.*?)결정\s*사항", r"결정\s*사항(.*)"),
            ]
            
            for disc_pattern, dec_pattern in patterns:
                if not discussion_text:
                    discussion_match = re.search(disc_pattern, text, re.DOTALL)
                    if discussion_match:
                        discussion_text = discussion_match.group(1).strip()
                
                if not decision_text:
                    decision_match = re.search(dec_pattern, text, re.DOTALL)
                    if decision_match:
                        decision_text = decision_match.group(1).strip()
                
                if discussion_text and decision_text:
                    break
            
            # 텍스트 정리
            if discussion_text:
                discussion_text = re.sub(r'\s+', ' ', discussion_text)[:5000]  # 최대 5000자
            if decision_text:
                decision_text = re.sub(r'\s+', ' ', decision_text)[:2000]  # 최대 2000자
            
            self.total_items += 1
            
            yield {
                'date': date,
                'year': year,
                'title': title,
                'content': text[:10000] if text else None,  # 전체 내용 (최대 10000자)
                'discussion': discussion_text,
                'decision': decision_text,
                'link': response.url,
                'pdf_pages': len(pdf_reader.pages),
                'extraction_success': bool(text)
            }
            
            self.logger.info(f"✅ 성공적으로 처리: {title} (페이지: {len(pdf_reader.pages)})")
            
        except Exception as e:
            self.logger.error(f"PDF 파싱 오류 {response.url}: {e}")
            # 오류 시에도 메타데이터는 수집
            yield {
                'date': response.meta.get('title'),
                'year': None,
                'title': response.meta.get('title'),
                'content': None,
                'discussion': None,
                'decision': None,
                'link': response.url,
                'pdf_pages': 0,
                'extraction_success': False,
                'error': str(e)
            }
    
    def closed(self, reason):
        """크롤링 종료 시 통계 출력"""
        self.logger.info("="*60)
        self.logger.info(f"MPB 의사록 크롤링 완료")
        self.logger.info(f"수집 기간: {self.start_year}년 ~ {self.end_year}년")
        self.logger.info(f"총 수집 항목: {self.total_items}개")
        self.logger.info("="*60)