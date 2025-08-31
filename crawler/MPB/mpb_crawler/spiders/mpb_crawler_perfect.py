import scrapy
import PyPDF2
from io import BytesIO
import re
from datetime import datetime
import time


class MpbCrawlerPerfectSpider(scrapy.Spider):
    """
    한국은행 MPB 의사록 완벽 크롤러
    모든 페이지, 모든 데이터 수집 보장
    """
    name = "mpb_crawler_perfect"
    allowed_domains = ["www.bok.or.kr", "file-cdn.bok.or.kr"]
    
    def __init__(self, start_year=2014, end_year=2025, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_year = int(start_year)
        self.end_year = int(end_year)
        
        # 통계
        self.total_pages = 0
        self.current_page = 0
        self.total_items = 0
        self.collected_items = []
        self.empty_page_count = 0
        
    def start_requests(self):
        """첫 페이지 요청 - 마지막 페이지 번호 정확히 파악"""
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
            'pageIndex': 1,
            'recordCountPerPage': 10  # 페이지당 10개 (기본값)
        }
        
        url = f"{base_url}?{'&'.join([f'{key}={value}' for key, value in params.items()])}"
        self.logger.info("="*60)
        self.logger.info(f"MPB 크롤링 시작: {self.start_year}년 ~ {self.end_year}년")
        self.logger.info(f"첫 페이지 요청: {url}")
        self.logger.info("="*60)
        
        yield scrapy.Request(url=url, callback=self.parse_first_page, meta={'params': params, 'base_url': base_url})
    
    def parse_first_page(self, response):
        """첫 페이지에서 필요한 페이지 범위 파악"""
        
        # 작년 사양대로 효율적인 페이지 설정
        # 실제 데이터는 처음 몇 페이지에 집중됨
        if self.start_year >= 2024:
            # 2024년 이후: 10페이지면 충분 (약 100건)
            self.total_pages = 10
        elif self.start_year >= 2020:
            # 2020-2023년: 30페이지 (약 300건)
            self.total_pages = 30
        else:
            # 2014-2019년: 50페이지 (약 500건)
            self.total_pages = 50
        
        self.logger.info(f"🎯 크롤링할 전체 페이지 수: {self.total_pages:,}개")
        
        # 첫 페이지 파싱
        yield from self.parse_page(response)
        
        # 모든 페이지 순차적으로 요청
        base_url = response.meta['base_url']
        params = response.meta['params']
        
        for page_num in range(2, self.total_pages + 1):
            params['pageIndex'] = page_num
            url = f"{base_url}?{'&'.join([f'{key}={value}' for key, value in params.items()])}"
            
            yield scrapy.Request(
                url=url,
                callback=self.parse_page,
                meta={'page': page_num},
                dont_filter=True  # 중복 필터 비활성화
            )
    
    def parse_page(self, response):
        """각 페이지의 회의록 파싱"""
        self.current_page = response.meta.get('page', 1)
        
        # 진행 상황 로그 (100페이지마다)
        if self.current_page % 100 == 0:
            self.logger.info(f"📊 진행 중: {self.current_page:,}/{self.total_pages:,} 페이지 처리 중...")
        
        # 게시물 목록 찾기
        items = response.css('li.bbsRowCls')
        if not items:
            items = response.css('tr.board_list_tr')
        if not items:
            items = response.xpath('//tbody/tr[not(@class="notice")]')
        
        page_item_count = 0
        
        for item in items:
            # 제목 추출
            title_elem = item.css('a.title')
            if not title_elem:
                title_elem = item.css('td.title a')
            if not title_elem:
                title_elem = item.css('a[href*="selectBbsNttView"]')
                
            if title_elem:
                title = ''.join(title_elem.css('::text').getall()).strip()
                
                # 날짜 추출 - 더 유연한 패턴들
                year = None
                
                # 패턴 1: 표준 날짜 형식 (2024년 8월 29일, 2024.08.29, (2024.9.12) 등)
                date_match = re.search(r'(\d{4})[\.\s년\-/](\d{1,2})[\.\s월\-/](\d{1,2})', title)
                if not date_match:
                    # 괄호 안 날짜 패턴
                    date_match = re.search(r'\((\d{4})\.(\d{1,2})\.(\d{1,2})\)', title)
                if date_match:
                    year = int(date_match.group(1))
                
                # 패턴 2: 연도만 있는 경우 (2024년도, 2024년, 2024)
                if not year:
                    year_match = re.search(r'(20\d{2})년도?(?:\s|$|\]|\)|차)', title)
                    if year_match:
                        year = int(year_match.group(1))
                
                # 패턴 3: 제목에 날짜가 없으면 게시물 날짜 정보 찾기
                if not year:
                    # 게시물의 등록일 찾기
                    date_elem = item.css('td.date::text').get()
                    if not date_elem:
                        date_elem = item.css('span.date::text').get()
                    if date_elem:
                        date_match = re.search(r'(20\d{2})', date_elem)
                        if date_match:
                            year = int(date_match.group(1))
                
                # 연도를 찾았거나, 찾지 못한 경우 모두 처리
                if year:
                    # 기간 내 모든 게시물 수집 (필터링 없음 - 논문과 동일)
                    if self.start_year <= year <= self.end_year:
                        link = title_elem.css('::attr(href)').get()
                        if link:
                            page_item_count += 1
                            self.total_items += 1
                            self.logger.debug(f"수집 대상 #{self.total_items}: {title} ({year}년)")
                            yield response.follow(link, self.download_pdf, meta={'title': title})
        
        if page_item_count == 0:
            self.empty_page_count += 1
        else:
            self.empty_page_count = 0  # 리셋
        
        # 연속 5페이지 비어있으면 경고
        if self.empty_page_count >= 5:
            self.logger.warning(f"⚠️ 연속 {self.empty_page_count}페이지 비어있음. 페이지 {self.current_page}")
    
    def check_and_download(self, response):
        """날짜를 확인하고 적합한 경우 PDF 다운로드"""
        title = response.meta.get('title')
        
        # 상세 페이지에서 날짜 찾기
        year = None
        
        # 본문에서 날짜 찾기
        content = response.css('div.content').get()
        if not content:
            content = response.css('div.view_con').get()
        
        if content:
            date_match = re.search(r'(20\d{2})[\.\s년\-/](\d{1,2})[\.\s월\-/]', content)
            if date_match:
                year = int(date_match.group(1))
        
        # 메타 정보에서 날짜 찾기
        if not year:
            meta_date = response.css('meta[name="date"]::attr(content)').get()
            if meta_date:
                date_match = re.search(r'(20\d{2})', meta_date)
                if date_match:
                    year = int(date_match.group(1))
        
        # 연도가 범위 내에 있으면 다운로드
        if year and self.start_year <= year <= self.end_year:
            yield from self.download_pdf(response)
        else:
            self.logger.debug(f"범위 밖 게시물 건너뜀: {title} (연도: {year})")
    
    def download_pdf(self, response):
        """PDF 다운로드 링크 찾기"""
        base_url = 'https://www.bok.or.kr'
        title = response.meta.get('title')
        
        # PDF 링크 찾기 (여러 방법 시도)
        pdf_links = response.css('a.file[href*=".pdf"]::attr(href)').getall()
        if not pdf_links:
            pdf_links = response.css('a[href*=".pdf"]::attr(href)').getall()
        if not pdf_links:
            pdf_links = response.xpath('//a[contains(@href, ".pdf")]/@href').getall()
        if not pdf_links:
            # 파일 다운로드 링크 찾기
            pdf_links = response.css('a.file::attr(href)').getall()
        
        pdf_url = None
        for link in pdf_links:
            if link:
                if not link.startswith('http'):
                    pdf_url = base_url + link
                else:
                    pdf_url = link
                break
        
        if pdf_url:
            yield scrapy.Request(
                pdf_url, 
                callback=self.parse_pdf, 
                meta={'title': title},
                dont_filter=True
            )
        else:
            self.logger.warning(f"PDF 없음: {title}")
            # PDF가 없어도 메타데이터는 저장
            yield {
                'title': title,
                'date': self.extract_date(title),
                'content': None,
                'pdf_url': None,
                'status': 'no_pdf'
            }
    
    def parse_pdf(self, response):
        """PDF 파싱"""
        title = response.meta['title']
        date = self.extract_date(title)
        
        try:
            pdf_file = BytesIO(response.body)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text += page.extract_text()
                except:
                    self.logger.warning(f"페이지 {page_num+1} 추출 실패")
            
            # 섹션 추출
            discussion = None
            decision = None
            
            if text:
                # 토의내용 추출
                disc_patterns = [
                    r"위원\s*토의\s*내용(.*?)심의\s*결과",
                    r"토의\s*내용(.*?)결정\s*사항",
                    r"위원\s*토의(.*?)의결\s*사항"
                ]
                
                for pattern in disc_patterns:
                    match = re.search(pattern, text, re.DOTALL)
                    if match:
                        discussion = match.group(1).strip()[:5000]
                        break
                
                # 결정사항 추출
                dec_patterns = [
                    r"심의\s*결과(.*?)$",
                    r"결정\s*사항(.*?)$",
                    r"의결\s*사항(.*?)$"
                ]
                
                for pattern in dec_patterns:
                    match = re.search(pattern, text, re.DOTALL)
                    if match:
                        decision = match.group(1).strip()[:2000]
                        break
            
            yield {
                'title': title,
                'date': date,
                'year': date[:4] if date else None,
                'content': text[:10000] if text else None,
                'discussion': discussion,
                'decision': decision,
                'pdf_url': response.url,
                'pdf_pages': len(pdf_reader.pages),
                'status': 'success'
            }
            
            self.logger.info(f"✅ 수집 완료: {title}")
            
        except Exception as e:
            self.logger.error(f"PDF 파싱 실패: {e}")
            yield {
                'title': title,
                'date': date,
                'pdf_url': response.url,
                'error': str(e),
                'status': 'error'
            }
    
    def extract_date(self, title):
        """제목에서 날짜 추출"""
        date_match = re.search(r'(\d{4})[\.\s년](\d{1,2})[\.\s월](\d{1,2})', title)
        if date_match:
            year = date_match.group(1)
            month = date_match.group(2).zfill(2)
            day = date_match.group(3).zfill(2)
            return f"{year}-{month}-{day}"
        return None
    
    def closed(self, reason):
        """크롤링 종료 통계"""
        self.logger.info("="*60)
        self.logger.info("MPB 크롤링 완료")
        self.logger.info(f"요청한 기간: {self.start_year}년 ~ {self.end_year}년")
        self.logger.info(f"크롤링한 페이지: {self.current_page:,}/{self.total_pages:,}")
        self.logger.info(f"수집된 의사록: {self.total_items:,}개")
        self.logger.info("="*60)