import scrapy
import json
import re
from datetime import datetime, timedelta
from urllib.parse import urlencode


class CallRatingsCompleteSpider(scrapy.Spider):
    """
    대한상공회의소 콜금리 완전 크롤러
    2014-2025년 모든 데이터 수집 보장
    """
    name = "call_ratings_complete"
    allowed_domains = ["www.korcham.net"]
    
    def __init__(self, start_date="2014-01-01", end_date="2025-12-31", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        
        # 통계
        self.total_pages = 0
        self.total_records = 0
        self.collected_dates = set()
        
    def start_requests(self):
        """초기 요청 - 전체 데이터 범위 파악"""
        base_url = 'https://www.korcham.net/nCham/Service/EconBrief/appl/ProspectBoardList.asp'
        
        # 날짜 형식: YYYYMMDD
        start_str = self.start_date.strftime("%Y%m%d")
        end_str = self.end_date.strftime("%Y%m%d")
        
        # 첫 페이지 요청으로 전체 구조 파악
        params = {
            'board_type': '1',
            'daybt': 'OldNow',
            'm_OldDate': start_str,
            'm_NowDate': end_str,
            'pageno': '1'
        }
        
        url = f"{base_url}?{urlencode(params)}"
        self.logger.info(f"콜금리 크롤링 시작: {self.start_date.date()} ~ {self.end_date.date()}")
        self.logger.info(f"요청 URL: {url}")
        
        yield scrapy.Request(
            url=url, 
            callback=self.parse_first_page,
            meta={'params': params, 'base_url': base_url}
        )
    
    def parse_first_page(self, response):
        """첫 페이지에서 전체 페이지 수 파악"""
        try:
            # 전체 레코드 수 추출
            total_text = response.css('div.board_info::text').get()
            if not total_text:
                # 다른 셀렉터 시도
                total_text = response.xpath('//div[contains(@class, "total")]//text()').get()
            
            total_records = None
            if total_text:
                # "총 2,866건" 같은 패턴에서 숫자 추출
                numbers = re.findall(r'[\d,]+', total_text)
                if numbers:
                    for num_str in numbers:
                        num = int(num_str.replace(',', ''))
                        if num > 100:  # 100 이상의 숫자만 전체 개수로 간주
                            total_records = num
                            break
                    if total_records:
                        self.logger.info(f"전체 레코드 수: {total_records:,}개")
            
            # 페이지네이션 분석
            pagination = response.css('div.paging')
            if pagination:
                # JavaScript page() 함수의 최대값 찾기
                page_links = pagination.css('a::attr(href)').getall()
                page_numbers = []
                
                for link in page_links:
                    # javascript:page('16') 패턴에서 숫자 추출
                    match = re.search(r"page\(['\"]?(\d+)['\"]?\)", link)
                    if match:
                        page_numbers.append(int(match.group(1)))
                
                # 페이지 번호 직접 추출 (텍스트에서)
                page_texts = pagination.css('a::text').getall()
                for text in page_texts:
                    if text.strip().isdigit():
                        page_numbers.append(int(text.strip()))
                
                if page_numbers:
                    max_page = max(page_numbers)
                    self.logger.info(f"최대 페이지: {max_page}")
                else:
                    # 레코드 수로 페이지 계산 (페이지당 15개 가정)
                    # 실제 웹사이트: 2,866건 / 15 = 192페이지
                    if total_records:
                        max_page = (total_records // 15) + (1 if total_records % 15 > 0 else 0)
                    else:
                        max_page = 192  # 실제 데이터 기준
                    self.logger.info(f"추정 페이지 수: {max_page}")
            else:
                # 페이지네이션이 없으면 실제 데이터 기준
                max_page = 192  # 2,866건 / 15 = 192페이지
                self.logger.warning("페이지네이션을 찾을 수 없음. 실제 데이터 기준 192페이지 사용")
            
            self.total_pages = max_page
            
            # 첫 페이지 파싱
            yield from self.parse_data(response)
            
            # 나머지 페이지 요청
            base_url = response.meta['base_url']
            params = response.meta['params']
            
            for page_num in range(2, max_page + 1):
                params['pageno'] = str(page_num)
                url = f"{base_url}?{urlencode(params)}"
                
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_data,
                    meta={'page': page_num}
                )
                
        except Exception as e:
            self.logger.error(f"첫 페이지 파싱 오류: {e}")
            # 오류 시에도 기본 크롤링 시도
            yield from self.fallback_crawl(response)
    
    def parse_data(self, response):
        """데이터 테이블 파싱"""
        # 테이블 찾기 (여러 셀렉터 시도)
        tables = response.css('table.board_list, table.list_table, div.tablewrap table')
        
        if not tables:
            # 모든 테이블 검색
            tables = response.css('table')
            
        for table in tables:
            rows = table.css('tbody tr')
            if not rows:
                rows = table.css('tr')
            
            for row in rows:
                # 헤더 행 제외
                if row.css('th'):
                    continue
                    
                cells = row.css('td::text').getall()
                if not cells:
                    cells = row.css('td *::text').getall()
                
                # 데이터가 있는 행만 처리 (최소 2개 셀)
                if len(cells) >= 2:
                    # 날짜 형식 확인 (YYYY.MM.DD 또는 YYYY-MM-DD)
                    date_text = cells[0].strip()
                    if re.match(r'\d{4}[\.-]\d{2}[\.-]\d{2}', date_text):
                        
                        # 날짜 정규화
                        date_normalized = date_text.replace('.', '-')
                        
                        # 날짜 범위 확인
                        try:
                            date_obj = datetime.strptime(date_normalized, '%Y-%m-%d')
                            if self.start_date <= date_obj <= self.end_date:
                                
                                # 중복 체크
                                if date_normalized not in self.collected_dates:
                                    self.collected_dates.add(date_normalized)
                                    self.total_records += 1
                                    
                                    # 데이터 구조화
                                    data = {
                                        '날짜': date_normalized,
                                        '콜금리': cells[1].strip() if len(cells) > 1 else None,
                                        'CD(91일)': cells[2].strip() if len(cells) > 2 else None,
                                        '국고채(3년)': cells[3].strip() if len(cells) > 3 else None,
                                        '국고채(5년)': cells[4].strip() if len(cells) > 4 else None,
                                        '회사채(3년,AA-)': cells[5].strip() if len(cells) > 5 else None,
                                        '원본': cells  # 디버깅용
                                    }
                                    
                                    yield data
                                    
                        except ValueError as e:
                            self.logger.warning(f"날짜 파싱 오류: {date_text} - {e}")
        
        page_num = response.meta.get('page', 1)
        self.logger.info(f"페이지 {page_num} 처리 완료: {len(self.collected_dates)}개 수집")
    
    def fallback_crawl(self, response):
        """폴백: 모든 페이지 크롤링"""
        base_url = response.meta.get('base_url')
        params = response.meta.get('params')
        
        # 실제 데이터 기준 192페이지까지 시도
        self.logger.warning("폴백 모드: 192페이지까지 크롤링 시도")
        
        for page_num in range(2, 193):
            params['pageno'] = str(page_num)
            url = f"{base_url}?{urlencode(params)}"
            
            yield scrapy.Request(
                url=url,
                callback=self.parse_data,
                meta={'page': page_num},
                dont_filter=True,  # 중복 필터 무시
                errback=self.handle_error
            )
    
    def handle_error(self, failure):
        """에러 처리"""
        page = failure.request.meta.get('page', 'unknown')
        self.logger.error(f"페이지 {page} 요청 실패: {failure.value}")
    
    def closed(self, reason):
        """크롤링 종료 시 통계"""
        self.logger.info("="*60)
        self.logger.info("콜금리 크롤링 완료")
        self.logger.info(f"수집 기간: {self.start_date.date()} ~ {self.end_date.date()}")
        self.logger.info(f"총 페이지: {self.total_pages}개")
        self.logger.info(f"총 레코드: {self.total_records}개")
        self.logger.info(f"수집된 고유 날짜: {len(self.collected_dates)}개")
        
        # 날짜 연속성 검증
        if self.collected_dates:
            dates_sorted = sorted([datetime.strptime(d, '%Y-%m-%d') for d in self.collected_dates])
            date_gaps = []
            
            for i in range(1, len(dates_sorted)):
                diff = (dates_sorted[i] - dates_sorted[i-1]).days
                if diff > 7:  # 주말 제외하고 7일 이상 차이
                    date_gaps.append((dates_sorted[i-1].date(), dates_sorted[i].date(), diff))
            
            if date_gaps:
                self.logger.warning(f"데이터 갭 발견: {len(date_gaps)}개")
                for start, end, days in date_gaps[:5]:  # 최대 5개만 표시
                    self.logger.warning(f"  {start} ~ {end}: {days}일 차이")
        
        self.logger.info("="*60)