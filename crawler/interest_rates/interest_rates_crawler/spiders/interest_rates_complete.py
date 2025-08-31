import scrapy
import json
import re
from datetime import datetime, timedelta
from urllib.parse import urlencode


class InterestRatesCompleteSpider(scrapy.Spider):
    """
    한국은행 기준금리 완전 크롤러
    2014-2025년 모든 데이터 수집
    JavaScript 변수에서 직접 데이터 추출
    """
    name = "interest_rates_complete"
    allowed_domains = ["www.bok.or.kr"]
    
    def __init__(self, start_year=2014, end_year=2025, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_year = int(start_year)
        self.end_year = int(end_year)
        
        # 통계
        self.total_records = 0
        self.rate_changes = []
        
    def start_requests(self):
        """한국은행 기준금리 페이지 요청"""
        # 메인 페이지
        url = 'https://www.bok.or.kr/portal/singl/baseRate/list.do?dataSeCd=01&menuNo=200643'
        
        self.logger.info(f"기준금리 크롤링 시작: {self.start_year}년 ~ {self.end_year}년")
        
        yield scrapy.Request(
            url=url,
            callback=self.parse_main_page,
            meta={'main_url': url}
        )
        
        # 추가 데이터 소스: 과거 데이터 페이지 (있을 경우)
        history_url = 'https://www.bok.or.kr/portal/singl/baseRate/histList.do?dataSeCd=01&menuNo=200643'
        yield scrapy.Request(
            url=history_url,
            callback=self.parse_history_page,
            errback=self.handle_error,
            dont_filter=True
        )
    
    def parse_main_page(self, response):
        """메인 페이지에서 JavaScript 변수 추출"""
        try:
            # JavaScript 변수 찾기: chartObj2_s = [{date:"2008-10-09", rate:5.25}, ...]
            script_texts = response.css('script::text').getall()
            
            all_data_found = False
            
            for script in script_texts:
                # chartObj2_s 변수 찾기 (모든 기준금리 변경 내역)
                if 'chartObj2_s' in script:
                    # 정규식으로 데이터 배열 추출
                    pattern = r'chartObj2_s\s*=\s*(\[[\s\S]*?\]);'
                    match = re.search(pattern, script)
                    
                    if match:
                        data_str = match.group(1)
                        # JavaScript 객체를 JSON으로 변환
                        # {date:"2008-10-09", rate:5.25} -> {"date":"2008-10-09", "rate":5.25}
                        data_str = re.sub(r'(\w+):', r'"\1":', data_str)  # key에 따옴표 추가
                        data_str = re.sub(r"'", '"', data_str)  # 작은따옴표를 큰따옴표로
                        
                        try:
                            data = json.loads(data_str)
                            self.logger.info(f"JavaScript 변수에서 {len(data)}개 데이터 발견")
                            all_data_found = True
                            
                            # 모든 데이터 처리 (2014-2025년 약 20개 변경 내역)
                            for item in data:
                                year = int(item['date'][:4])
                                if self.start_year <= year <= self.end_year:
                                    yield self.format_rate_data(item)
                                    
                        except json.JSONDecodeError:
                            # JSON 파싱 실패 시 수동 파싱
                            self.logger.warning("JSON 파싱 실패, 수동 파싱 시도")
                            yield from self.manual_parse_js_data(data_str)
                            all_data_found = True
            
            if not all_data_found:
                self.logger.warning("JavaScript 데이터를 찾을 수 없음, HTML 테이블 파싱 시도")
            
            # HTML 테이블에서도 데이터 추출 시도
            yield from self.parse_table_data(response)
            
        except Exception as e:
            self.logger.error(f"메인 페이지 파싱 오류: {e}")
            # 테이블 파싱으로 폴백
            yield from self.parse_table_data(response)
    
    def manual_parse_js_data(self, data_str):
        """JavaScript 데이터 수동 파싱"""
        # {date:"2008-10-09", rate:5.25} 패턴 찾기
        pattern = r'\{date:\s*"([^"]+)",\s*rate:\s*([\d.]+)\}'
        matches = re.findall(pattern, data_str)
        
        for date_str, rate_str in matches:
            try:
                year = int(date_str[:4])
                if self.start_year <= year <= self.end_year:
                    yield {
                        '연도': str(year),
                        '날짜': date_str,
                        '기준금리': f"{float(rate_str):.2f}%",
                        '변동폭': None,
                        '출처': 'JavaScript'
                    }
                    self.total_records += 1
            except (ValueError, IndexError) as e:
                self.logger.warning(f"데이터 파싱 오류: {date_str}, {rate_str} - {e}")
    
    def parse_table_data(self, response):
        """HTML 테이블에서 데이터 추출"""
        # 테이블 찾기
        tables = response.css('div.table table, table.tbl, table')
        
        for table in tables:
            rows = table.css('tbody tr')
            if not rows:
                rows = table.css('tr')
            
            for row in rows:
                # 헤더 제외
                if row.css('th'):
                    continue
                
                cells = row.css('td::text').getall()
                if not cells:
                    cells = row.css('td *::text').getall()
                
                # 기준금리 데이터 형식: 연도, 날짜, 금리
                if len(cells) >= 3:
                    year_text = cells[0].strip()
                    date_text = cells[1].strip()
                    rate_text = cells[2].strip()
                    
                    # 연도 확인
                    try:
                        if year_text.isdigit():
                            year = int(year_text)
                        elif date_text and len(date_text) >= 4:
                            year = int(date_text[:4])
                        else:
                            continue
                        
                        if self.start_year <= year <= self.end_year:
                            yield {
                                '연도': str(year),
                                '날짜': date_text,
                                '기준금리': rate_text,
                                '변동폭': cells[3].strip() if len(cells) > 3 else None,
                                '출처': 'HTML Table'
                            }
                            self.total_records += 1
                            
                    except (ValueError, IndexError):
                        continue
    
    def parse_history_page(self, response):
        """과거 데이터 페이지 파싱"""
        self.logger.info("과거 데이터 페이지 확인")
        
        # 연도별 링크 찾기
        year_links = response.css('a[href*="year="]::attr(href)').getall()
        
        for link in year_links:
            # year=2014 같은 패턴에서 연도 추출
            year_match = re.search(r'year=(\d{4})', link)
            if year_match:
                year = int(year_match.group(1))
                if self.start_year <= year <= self.end_year:
                    yield response.follow(link, self.parse_year_data, meta={'year': year})
        
        # 페이지네이션 확인
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse_history_page)
    
    def parse_year_data(self, response):
        """특정 연도 데이터 파싱"""
        year = response.meta.get('year')
        self.logger.info(f"{year}년 데이터 파싱")
        
        # 테이블 데이터 추출
        yield from self.parse_table_data(response)
    
    def format_rate_data(self, item):
        """데이터 포맷팅"""
        date = item.get('date', '')
        rate = item.get('rate', 0)
        
        # 이전 금리와 비교하여 변동폭 계산
        if self.rate_changes:
            prev_rate = self.rate_changes[-1]['rate']
            change = rate - prev_rate
            change_str = f"{change:+.2f}%p" if change != 0 else "-"
        else:
            change_str = "-"
        
        self.rate_changes.append({'date': date, 'rate': rate})
        self.total_records += 1
        
        return {
            '연도': date[:4] if date else '',
            '날짜': date,
            '기준금리': f"{rate:.2f}%",
            '변동폭': change_str,
            '출처': 'JavaScript'
        }
    
    def handle_error(self, failure):
        """에러 처리"""
        self.logger.error(f"요청 실패: {failure.value}")
    
    def closed(self, reason):
        """크롤링 종료 시 통계"""
        self.logger.info("="*60)
        self.logger.info("기준금리 크롤링 완료")
        self.logger.info(f"수집 기간: {self.start_year}년 ~ {self.end_year}년")
        self.logger.info(f"총 레코드: {self.total_records}개")
        
        if self.rate_changes:
            # 금리 변동 통계
            rates = [r['rate'] for r in self.rate_changes]
            self.logger.info(f"최고 금리: {max(rates):.2f}%")
            self.logger.info(f"최저 금리: {min(rates):.2f}%")
            self.logger.info(f"금리 변경 횟수: {len(self.rate_changes)}회")
            
            # 연도별 금리 변경 횟수
            year_counts = {}
            for item in self.rate_changes:
                year = item['date'][:4]
                year_counts[year] = year_counts.get(year, 0) + 1
            
            self.logger.info("연도별 금리 변경:")
            for year in sorted(year_counts.keys()):
                if int(year) >= self.start_year and int(year) <= self.end_year:
                    self.logger.info(f"  {year}년: {year_counts[year]}회")
        
        self.logger.info("="*60)