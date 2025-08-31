#!/usr/bin/env python3
"""
통합 뉴스 크롤러 (안전 강화 버전)
네이버 검색 제한 우회를 위한 개선된 크롤러
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime, timedelta
from urllib.parse import quote, urljoin
import os
import logging
from typing import List, Dict, Optional
import hashlib

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class SafeUnifiedNewsCrawler:
    """안전 강화 통합 뉴스 크롤러"""
    
    # User-Agent 리스트 (다양한 브라우저/OS 조합)
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0'
    ]
    
    def __init__(self, keyword="금리", safe_mode=True):
        self.keyword = keyword
        self.safe_mode = safe_mode
        self.collected_urls = set()
        self.session = None
        self.retry_count = 0
        self.max_retries = 3
        
        # 안전 모드 설정
        if self.safe_mode:
            self.min_delay = 2.0  # 최소 대기 시간 (초)
            self.max_delay = 5.0  # 최대 대기 시간 (초)
            self.page_size = 5    # 페이지당 아이템 수 감소
        else:
            self.min_delay = 1.0
            self.max_delay = 2.0
            self.page_size = 10
        
        # 세션 초기화
        self.reset_session()
    
    def reset_session(self):
        """세션 재생성 및 초기화"""
        if self.session:
            self.session.close()
        
        self.session = requests.Session()
        
        # 랜덤 User-Agent 선택
        user_agent = random.choice(self.USER_AGENTS)
        
        # 헤더 설정 (더 자연스럽게)
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        # 네이버 메인 방문하여 쿠키 획득
        try:
            logger.info(f"새 세션 생성 (User-Agent: {user_agent[:50]}...)")
            self.session.get('https://www.naver.com', timeout=10)
            self.random_delay()  # 메인 페이지 방문 후 대기
        except:
            logger.warning("네이버 메인 접속 실패, 계속 진행")
    
    def random_delay(self, multiplier=1.0):
        """랜덤 대기 시간"""
        delay = random.uniform(self.min_delay, self.max_delay) * multiplier
        logger.debug(f"대기: {delay:.2f}초")
        time.sleep(delay)
    
    def safe_request(self, url, params=None, max_retries=None):
        """안전한 요청 처리 (재시도 메커니즘 포함)"""
        if max_retries is None:
            max_retries = self.max_retries
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # 재시도 시 대기시간 증가 (exponential backoff)
                if attempt > 0:
                    wait_time = (2 ** attempt) * random.uniform(2, 4)
                    logger.warning(f"재시도 {attempt+1}/{max_retries}, {wait_time:.1f}초 대기...")
                    time.sleep(wait_time)
                    
                    # 3번째 시도부터는 세션 재생성
                    if attempt >= 2:
                        logger.info("세션 재생성...")
                        self.reset_session()
                
                response = self.session.get(url, params=params, timeout=15)
                
                # 성공 코드 확인
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    logger.warning(f"Rate limit detected (429). Waiting longer...")
                    time.sleep(30)  # Rate limit 시 30초 대기
                    self.reset_session()
                elif response.status_code == 503:
                    logger.warning(f"Service unavailable (503). Retrying...")
                    time.sleep(10)
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt+1}")
                last_error = "Timeout"
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error on attempt {attempt+1}")
                last_error = "Connection Error"
                self.reset_session()
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                last_error = str(e)
        
        logger.error(f"모든 재시도 실패: {last_error}")
        return None
    
    def crawl_yonhap(self, start_date: str, end_date: str) -> List[Dict]:
        """연합뉴스 크롤링 (안전 강화)"""
        articles = []
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 2014년은 수집 불가
        if start_dt.year <= 2014:
            logger.warning(f"연합뉴스 {start_dt.year}년 데이터는 네이버에서 제공하지 않습니다")
            return []
        
        # 날짜 형식 변환
        ds = start_dt.strftime('%Y.%m.%d')
        de = end_dt.strftime('%Y.%m.%d')
        nso_from = start_dt.strftime('%Y%m%d')
        nso_to = end_dt.strftime('%Y%m%d')
        
        logger.info(f"연합뉴스 검색: {start_date} ~ {end_date}")
        
        page = 0
        empty_page_count = 0
        consecutive_errors = 0
        
        while empty_page_count < 3 and consecutive_errors < 3:
            # 페이지당 결과 수를 줄여서 요청
            start_idx = page * self.page_size + 1
            
            url = "https://search.naver.com/search.naver"
            params = {
                'where': 'news',
                'query': f'연합뉴스 {self.keyword}',
                'ds': ds,
                'de': de,
                'nso': f'so:r,p:from{nso_from}to{nso_to}',
                'start': str(start_idx),
                'news_office_checked': '1001',  # 연합뉴스 코드
                'nso_open': '1'
            }
            
            # 안전한 요청
            response = self.safe_request(url, params)
            
            if response and response.status_code == 200:
                consecutive_errors = 0  # 성공 시 에러 카운트 리셋
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 연합뉴스 링크 찾기
                yonhap_links = []
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if 'yna.co.kr' in href or 'yonhapnews.co.kr' in href:
                        url_hash = hashlib.md5(href.encode()).hexdigest()
                        if url_hash not in self.collected_urls:
                            self.collected_urls.add(url_hash)
                            yonhap_links.append(href)
                
                if not yonhap_links:
                    empty_page_count += 1
                    logger.info(f"  페이지 {page+1}: 더 이상 결과 없음")
                else:
                    empty_page_count = 0
                    logger.info(f"  페이지 {page+1}: {len(yonhap_links)}개 발견")
                    
                    # 각 링크에서 기사 추출 (대기시간 포함)
                    for idx, link in enumerate(yonhap_links):
                        if idx > 0 and idx % 3 == 0:  # 3개마다 추가 대기
                            self.random_delay(multiplier=1.5)
                        
                        article = self.extract_yonhap_article(link)
                        if article:
                            # 날짜 확인
                            if article.get('date'):
                                try:
                                    article_date = datetime.strptime(article['date'], '%Y-%m-%d')
                                    if start_dt.date() <= article_date.date() <= end_dt.date():
                                        articles.append(article)
                                        logger.info(f"    ✓ {article['title'][:50]}...")
                                except:
                                    pass
                        
                        # 각 기사 추출 후 짧은 대기
                        self.random_delay(multiplier=0.5)
                
                page += 1
                
                # 페이지 간 대기 (안전 모드)
                self.random_delay(multiplier=1.5)
                
                # 10페이지마다 세션 재생성
                if page > 0 and page % 10 == 0:
                    logger.info("10페이지 처리 완료, 세션 재생성...")
                    self.reset_session()
                    self.random_delay(multiplier=2.0)
                    
            else:
                consecutive_errors += 1
                logger.warning(f"요청 실패, 연속 에러: {consecutive_errors}")
        
        return articles
    
    def extract_yonhap_article(self, url: str) -> Optional[Dict]:
        """연합뉴스 기사 추출"""
        try:
            response = self.safe_request(url)
            
            if not response or response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 제목 추출
            title = None
            title_selectors = [
                'h1.tit',
                'h1.headline',
                'h2.tit',
                'meta[property="og:title"]'
            ]
            
            for selector in title_selectors:
                elem = soup.select_one(selector)
                if elem:
                    if selector.startswith('meta'):
                        title = elem.get('content', '')
                    else:
                        title = elem.get_text(strip=True)
                    if title and len(title) > 5:
                        break
            
            if not title:
                return None
            
            # 본문 추출
            content = ""
            content_selectors = [
                'article.article-wrap01',
                'article.story-news',
                'div.article-txt',
                'div#articleBodyContents',
                'div.news-view-body'
            ]
            
            for selector in content_selectors:
                elem = soup.select_one(selector)
                if elem:
                    paragraphs = elem.find_all('p')
                    if paragraphs:
                        content_parts = []
                        for p in paragraphs:
                            text = p.get_text(strip=True)
                            if text and not text.startswith('※'):
                                content_parts.append(text)
                        content = ' '.join(content_parts)
                    else:
                        texts = elem.find_all(text=True, recursive=True)
                        content = ' '.join([t.strip() for t in texts if t.strip()])
                    
                    if len(content) > 100:
                        break
            
            # 키워드 확인
            if self.keyword not in title and self.keyword not in content:
                return None
            
            # 날짜 추출
            date = self.extract_date(soup, url)
            
            return {
                'title': title,
                'content': content[:3000],
                'date': date,
                'url': url,
                'source': 'yonhap',
                'keyword': self.keyword,
                'content_length': len(content)
            }
            
        except Exception as e:
            logger.error(f"연합뉴스 기사 추출 오류 ({url}): {e}")
            return None
    
    def crawl_edaily(self, start_date: str, end_date: str) -> List[Dict]:
        """이데일리 크롤링 (안전 강화)"""
        articles = []
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 날짜 형식 변환
        ds = start_dt.strftime('%Y.%m.%d')
        de = end_dt.strftime('%Y.%m.%d')
        nso_from = start_dt.strftime('%Y%m%d')
        nso_to = end_dt.strftime('%Y%m%d')
        
        logger.info(f"이데일리 검색: {start_date} ~ {end_date}")
        
        page = 0
        empty_page_count = 0
        consecutive_errors = 0
        
        while empty_page_count < 3 and consecutive_errors < 3:
            start_idx = page * self.page_size + 1
            
            url = "https://search.naver.com/search.naver"
            params = {
                'where': 'news',
                'query': f'이데일리 {self.keyword}',
                'ds': ds,
                'de': de,
                'nso': f'so:r,p:from{nso_from}to{nso_to}',
                'start': str(start_idx),
                'news_office_checked': '1018',  # 이데일리 코드
                'nso_open': '1'
            }
            
            response = self.safe_request(url, params)
            
            if response and response.status_code == 200:
                consecutive_errors = 0
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 이데일리 링크 찾기
                edaily_links = []
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if 'edaily.co.kr' in href and '/news/' in href:
                        if href.startswith('http://'):
                            href = href.replace('http://', 'https://')
                        
                        url_hash = hashlib.md5(href.encode()).hexdigest()
                        if url_hash not in self.collected_urls:
                            self.collected_urls.add(url_hash)
                            edaily_links.append(href)
                
                if not edaily_links:
                    empty_page_count += 1
                    logger.info(f"  페이지 {page+1}: 더 이상 결과 없음")
                else:
                    empty_page_count = 0
                    logger.info(f"  페이지 {page+1}: {len(edaily_links)}개 발견")
                    
                    # 각 링크에서 기사 추출
                    for idx, link in enumerate(edaily_links):
                        if idx > 0 and idx % 3 == 0:
                            self.random_delay(multiplier=1.5)
                        
                        article = self.extract_edaily_article(link)
                        if article:
                            if article.get('date'):
                                try:
                                    article_date = datetime.strptime(article['date'], '%Y-%m-%d')
                                    if start_dt.date() <= article_date.date() <= end_dt.date():
                                        articles.append(article)
                                        logger.info(f"    ✓ {article['title'][:50]}...")
                                except:
                                    pass
                        
                        self.random_delay(multiplier=0.5)
                
                page += 1
                self.random_delay(multiplier=1.5)
                
                # 10페이지마다 세션 재생성
                if page > 0 and page % 10 == 0:
                    logger.info("10페이지 처리 완료, 세션 재생성...")
                    self.reset_session()
                    self.random_delay(multiplier=2.0)
                    
            else:
                consecutive_errors += 1
                logger.warning(f"요청 실패, 연속 에러: {consecutive_errors}")
        
        return articles
    
    def extract_edaily_article(self, url: str) -> Optional[Dict]:
        """이데일리 기사 추출"""
        try:
            response = self.safe_request(url)
            
            if not response or response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 제목 추출
            title = None
            title_selectors = [
                'h1.news_titles',
                'h2.news_titles',
                'h1',
                'meta[property="og:title"]'
            ]
            
            for selector in title_selectors:
                elem = soup.select_one(selector)
                if elem:
                    if selector.startswith('meta'):
                        title = elem.get('content', '')
                    else:
                        title = elem.get_text(strip=True)
                    if title and len(title) > 5:
                        break
            
            if not title:
                return None
            
            # 본문 추출
            content = ""
            content_selectors = [
                'div.news_body',
                'div.article_body',
                'div#newsContent',
                'article'
            ]
            
            for selector in content_selectors:
                elem = soup.select_one(selector)
                if elem:
                    texts = elem.find_all(text=True, recursive=True)
                    content = ' '.join([t.strip() for t in texts if t.strip()])
                    if len(content) > 100:
                        break
            
            # 키워드 확인
            if self.keyword not in title and self.keyword not in content:
                return None
            
            # 날짜 추출
            date = self.extract_date(soup, url)
            
            return {
                'title': title,
                'content': content[:3000],
                'date': date,
                'url': url,
                'source': 'edaily',
                'keyword': self.keyword,
                'content_length': len(content)
            }
            
        except Exception as e:
            logger.error(f"이데일리 기사 추출 오류 ({url}): {e}")
            return None
    
    def crawl_infomax(self, start_date: str, end_date: str) -> List[Dict]:
        """인포맥스 크롤링 (직접 사이트 - 안전 강화)"""
        articles = []
        collected_titles = set()
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        logger.info(f"인포맥스 검색: {start_date} ~ {end_date}")
        
        start_str = start_dt.strftime('%Y%m%d')
        end_str = end_dt.strftime('%Y%m%d')
        
        page = 1
        empty_page_count = 0
        consecutive_errors = 0
        
        while empty_page_count < 3 and consecutive_errors < 3:
            url = "https://news.einfomax.co.kr/news/articleList.html"
            params = {
                'sc_word': self.keyword,
                'sc_sdate': start_str,
                'sc_edate': end_str,
                'page': str(page)
            }
            
            response = self.safe_request(url, params)
            
            if response and response.status_code == 200:
                consecutive_errors = 0
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 기사 링크 찾기
                article_links = []
                for a in soup.find_all('a', href=True):
                    href = a.get('href', '')
                    if '/articleView.html' in href:
                        if not href.startswith('http'):
                            href = urljoin('https://news.einfomax.co.kr', href)
                        
                        url_hash = hashlib.md5(href.encode()).hexdigest()
                        if url_hash not in self.collected_urls:
                            self.collected_urls.add(url_hash)
                            article_links.append(href)
                
                if not article_links:
                    empty_page_count += 1
                    logger.info(f"  페이지 {page}: 더 이상 결과 없음")
                else:
                    empty_page_count = 0
                    logger.info(f"  페이지 {page}: {len(article_links)}개 발견")
                
                page += 1
                
                # 각 링크에서 기사 추출
                for idx, link in enumerate(article_links):
                    if idx > 0 and idx % 3 == 0:
                        self.random_delay(multiplier=1.5)
                    
                    article = self.extract_infomax_article(link)
                    if article:
                        title_hash = hashlib.md5(article['title'].encode()).hexdigest()
                        if title_hash not in collected_titles:
                            collected_titles.add(title_hash)
                            
                            article_date = None
                            if article.get('date'):
                                try:
                                    article_date = datetime.strptime(article['date'], '%Y-%m-%d')
                                    if start_dt.date() <= article_date.date() <= end_dt.date():
                                        articles.append(article)
                                        logger.info(f"    ✓ {article['title'][:50]}...")
                                except:
                                    articles.append(article)
                                    logger.info(f"    ✓ {article['title'][:50]}...")
                    
                    self.random_delay(multiplier=0.5)
                
                self.random_delay(multiplier=1.0)
                
                # 10페이지마다 세션 재생성
                if page > 0 and page % 10 == 0:
                    logger.info("10페이지 처리 완료, 세션 재생성...")
                    self.reset_session()
                    self.random_delay(multiplier=2.0)
                    
            else:
                consecutive_errors += 1
                logger.warning(f"요청 실패, 연속 에러: {consecutive_errors}")
        
        return articles
    
    def extract_infomax_article(self, url: str) -> Optional[Dict]:
        """인포맥스 기사 추출"""
        try:
            response = self.safe_request(url)
            
            if not response or response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 제목 추출
            title_elem = soup.select_one('h3.heading')
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)
            
            # 본문 추출
            content_elem = soup.select_one('article#article-view-content-div')
            if not content_elem:
                return None
            
            texts = content_elem.find_all(text=True, recursive=True)
            content = ' '.join([t.strip() for t in texts if t.strip()])
            
            # 키워드 확인
            if self.keyword not in title and self.keyword not in content:
                return None
            
            # 날짜 추출
            date = None
            info_items = soup.select('ul.infomation li')
            for item in info_items:
                text = item.get_text().strip()
                if '입력' in text or '수정' in text:
                    date = self.parse_date(text)
                    if date:
                        break
            
            return {
                'title': title,
                'content': content[:3000],
                'date': date,
                'url': url,
                'source': 'infomax',
                'keyword': self.keyword,
                'content_length': len(content)
            }
            
        except Exception as e:
            logger.error(f"인포맥스 기사 추출 오류 ({url}): {e}")
            return None
    
    def extract_date(self, soup, url):
        """날짜 추출 (공통)"""
        date = None
        date_selectors = [
            'span.dates',
            'div.dates',
            'time',
            'meta[property="article:published_time"]',
            'span.date',
            'span.article-time',
            'span.update-time'
        ]
        
        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                if selector.startswith('meta'):
                    date_str = elem.get('content', '')
                elif elem.name == 'time':
                    date_str = elem.get('datetime', '') or elem.get_text(strip=True)
                else:
                    date_str = elem.get_text(strip=True)
                
                if date_str:
                    date = self.parse_date(date_str)
                    if date:
                        break
        
        # URL에서 날짜 추출 시도
        if not date:
            import re
            url_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
            if url_match:
                year, month, day = url_match.groups()
                date = f"{year}-{month}-{day}"
        
        return date
    
    def parse_date(self, date_str: str) -> Optional[str]:
        """날짜 문자열 파싱"""
        import re
        
        date_str = date_str.strip()
        
        patterns = [
            (r'(\d{4})[\-\.](\d{1,2})[\-\.](\d{1,2})', lambda m: f"{m[1]}-{m[2]:0>2}-{m[3]:0>2}"),
            (r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', lambda m: f"{m[1]}-{m[2]:0>2}-{m[3]:0>2}"),
            (r'(\d{8})', lambda m: f"{m[1][:4]}-{m[1][4:6]}-{m[1][6:8]}"),
        ]
        
        for pattern, formatter in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 1:
                        date_val = groups[0]
                        return f"{date_val[:4]}-{date_val[4:6]}-{date_val[6:8]}"
                    else:
                        year, month, day = groups[:3]
                        return f"{year}-{int(month):02d}-{int(day):02d}"
                except:
                    continue
        
        return None
    
    def crawl_all(self, start_date: str, end_date: str, sources=['yonhap', 'edaily', 'infomax']) -> Dict[str, List[Dict]]:
        """모든 소스에서 크롤링 (안전 모드)"""
        results = {}
        
        # 각 소스 크롤링 전 세션 재생성
        for source in sources:
            logger.info(f"\n=== {source.upper()} 크롤링 시작 ===")
            self.reset_session()
            self.random_delay(multiplier=2.0)  # 소스 전환 시 추가 대기
            
            if source == 'yonhap':
                articles = self.crawl_yonhap(start_date, end_date)
                results['yonhap'] = articles
                logger.info(f"연합뉴스: {len(articles)}개 수집")
            elif source == 'edaily':
                articles = self.crawl_edaily(start_date, end_date)
                results['edaily'] = articles
                logger.info(f"이데일리: {len(articles)}개 수집")
            elif source == 'infomax':
                articles = self.crawl_infomax(start_date, end_date)
                results['infomax'] = articles
                logger.info(f"인포맥스: {len(articles)}개 수집")
            
            # 소스 간 대기 (긴 휴지 시간)
            if source != sources[-1]:  # 마지막 소스가 아니면
                wait_time = random.uniform(10, 20)
                logger.info(f"다음 소스 크롤링 전 {wait_time:.1f}초 대기...")
                time.sleep(wait_time)
        
        return results
    
    def save_to_json(self, data: Dict, filename: str):
        """JSON 파일로 저장"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        total_articles = sum(len(articles) for articles in data.values())
        logger.info(f"저장 완료: {filename} (총 {total_articles}개)")


def main():
    """테스트 실행"""
    # 안전 모드로 크롤러 생성
    crawler = SafeUnifiedNewsCrawler(keyword="금리", safe_mode=True)
    
    # 짧은 기간 테스트
    print("\n" + "="*60)
    print("안전 모드 크롤링 테스트")
    print("="*60)
    
    results = crawler.crawl_all('2015-01-01', '2015-01-03')
    
    print("\n수집 결과:")
    for source, articles in results.items():
        print(f"  {source}: {len(articles)}개")
        if articles:
            print(f"    샘플: {articles[0]['title'][:50]}...")
    
    # 저장
    crawler.save_to_json(results, '/tmp/safe_crawler_test.json')


if __name__ == "__main__":
    main()