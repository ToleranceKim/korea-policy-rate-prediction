#!/usr/bin/env python3
"""
통합 뉴스 크롤러 - Scrapy 없이 작동
연합뉴스, 이데일리, 인포맥스 모두 지원
requests + BeautifulSoup 사용
"""
import requests
from bs4 import BeautifulSoup
import json
import time
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


class UnifiedNewsCrawler:
    """통합 뉴스 크롤러"""
    
    def __init__(self, keyword="금리"):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.keyword = keyword
        self.collected_urls = set()
        
        # 네이버 메인에서 쿠키 획득
        self.session.get('https://www.naver.com')
    
    def crawl_yonhap(self, start_date: str, end_date: str) -> List[Dict]:
        """연합뉴스 크롤링 - 일별 API 직접 요청 (2016년부터 가능)"""
        articles = []
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 2016년 이전은 네이버 뉴스 검색 사용
        if start_dt.year < 2016:
            logger.info(f"연합뉴스 {start_dt.year}년 데이터 - 네이버 뉴스 검색 사용")
            return self.crawl_yonhap_direct(start_date, end_date)
        
        logger.info(f"연합뉴스 API 크롤링: {start_date} ~ {end_date}")
        
        # 날짜별로 API 요청 (작년 로직)
        current_date = start_dt
        total_articles = 0
        
        while current_date <= end_dt:
            date_str = current_date.strftime('%Y%m%d')
            daily_articles = []
            
            # 페이지네이션 처리 (각 날짜별로 모든 페이지 순회)
            page_no = 1
            
            while True:  # 페이지 제한 없음
                # 연합뉴스 API URL
                url = 'http://ars.yna.co.kr/api/v2/search.asis'
                
                params = {
                    'callback': 'Search.SearchPreCallback',
                    'query': self.keyword,
                    'page_no': str(page_no),
                    'period': 'diy',
                    'from': date_str,
                    'to': date_str,
                    'ctype': 'A',
                    'page_size': '50',
                    'channel': 'basic_kr'
                }
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://www.yna.co.kr/'
                }
                
                try:
                    response = requests.get(url, params=params, headers=headers, timeout=20)
                    
                    if 'Search.SearchPreCallback' in response.text:
                        # JSONP 콜백 제거 및 JSON 파싱
                        import re
                        json_str = re.search(r'Search\.SearchPreCallback\((.*)\)', response.text)
                        if json_str:
                            data = json.loads(json_str.group(1))
                            results = data.get('KR_ARTICLE', {}).get('result', [])
                            
                            # 결과가 없으면 다음 날짜로
                            if not results:
                                break
                            
                            page_articles = []
                            for item in results:
                                # 날짜 확인 (API가 정확한 날짜를 반환하는지 체크)
                                article_date = item.get('DIST_DATE', '')
                                if article_date.startswith(date_str[:8]):
                                    # URL 생성 (CONTENTS_ID 사용)
                                    article_id = item.get('CONTENTS_ID', '')
                                    article_url = f"https://www.yna.co.kr/view/{article_id}" if article_id else ''
                                    
                                    # 본문은 TEXT_BODY 사용
                                    content = item.get('TEXT_BODY', item.get('CONTENTS', ''))
                                    
                                    article = {
                                        'title': item.get('TITLE', ''),
                                        'content': content,
                                        'date': f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}",
                                        'url': article_url,
                                        'source': 'yonhap',
                                        'keyword': self.keyword,
                                        'content_length': len(content)
                                    }
                                    
                                    # API가 본문을 제공하지 않거나 너무 짧은 경우 기사 페이지 직접 방문
                                    if (not article['content'] or article['content_length'] < 200) and article['url']:
                                        logger.debug(f"    콘텐츠 부족, URL 방문: {article['url']}")
                                        full_article = self.extract_yonhap_article(article['url'])
                                        if full_article and full_article.get('content'):
                                            article['content'] = full_article['content']
                                            article['content_length'] = len(full_article['content'])
                                            logger.debug(f"    콘텐츠 수집 성공: {len(full_article['content'])}자")
                                        else:
                                            logger.warning(f"    콘텐츠 수집 실패: {article['url']}")
                                    
                                    page_articles.append(article)
                            
                            # 이 페이지에서 수집한 기사를 전체 목록에 추가
                            daily_articles.extend(page_articles)
                            
                            # 이 페이지에서 날짜가 맞는 기사가 하나도 없으면 종료
                            # (API가 날짜순으로 정렬되어 있다고 가정)
                            if len(page_articles) == 0 and page_no > 1:
                                break
                            
                            # 결과가 없으면 마지막 페이지로 간주
                            if len(results) == 0:
                                break
                            
                            page_no += 1
                            time.sleep(0.3)  # 페이지 간 짧은 대기
                    
                except Exception as e:
                    logger.error(f"연합뉴스 API 오류 ({date_str}, 페이지 {page_no}): {e}")
                    break
            
            # 하루 수집 결과 정리
            if daily_articles:
                articles.extend(daily_articles)
                logger.info(f"  {current_date.strftime('%Y-%m-%d')}: {len(daily_articles)}개 수집")
                total_articles += len(daily_articles)
            
            time.sleep(0.5)  # 날짜 간 대기
            current_date += timedelta(days=1)
        
        logger.info(f"연합뉴스 총 {total_articles}개 기사 수집 완료")
        return articles
    
    def parse_date_from_text(self, date_text: str) -> Optional[str]:
        """날짜 텍스트를 파싱하여 YYYY-MM-DD 형식으로 변환"""
        import re
        from datetime import datetime, timedelta
        
        # 오늘, 어제 등 처리
        if '오늘' in date_text or '시간 전' in date_text or '분 전' in date_text:
            return datetime.now().strftime('%Y-%m-%d')
        elif '어제' in date_text:
            return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        elif '일 전' in date_text:
            days = re.search(r'(\d+)일 전', date_text)
            if days:
                return (datetime.now() - timedelta(days=int(days.group(1)))).strftime('%Y-%m-%d')
        
        # 2023.06.15. 형식
        match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})\.', date_text)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        
        # 2023-06-15 형식
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_text)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        
        return None
    
    def extract_yonhap_article(self, url: str) -> Optional[Dict]:
        """연합뉴스 기사 추출"""
        try:
            # 타임아웃 증가 및 재시도 로직 추가
            for attempt in range(3):
                try:
                    response = self.session.get(url, timeout=20)
                    break
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt == 2:
                        raise e
                    logger.warning(f"연합뉴스 재시도 {attempt+1}/3: {url}")
                    time.sleep(3 * (attempt + 1))  # 3초, 6초 대기
            
            if response.status_code != 200:
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
                'article.article-wrap01',  # 2015년 연합뉴스 실제 구조
                'article.story-news',
                'div.article-txt',
                'div#articleBodyContents',
                'div.news-view-body'
            ]
            
            for selector in content_selectors:
                elem = soup.select_one(selector)
                if elem:
                    # p 태그 위주로 본문 추출
                    paragraphs = elem.find_all('p')
                    if paragraphs:
                        content_parts = []
                        for p in paragraphs:
                            text = p.get_text(strip=True)
                            if text and not text.startswith('※'):
                                content_parts.append(text)
                        content = ' '.join(content_parts)
                    else:
                        # p 태그가 없으면 전체 텍스트 추출
                        texts = elem.find_all(text=True, recursive=True)
                        content = ' '.join([t.strip() for t in texts if t.strip()])
                    
                    if len(content) > 100:
                        break
            
            # 키워드 확인 제거 - API 검색 결과에 이미 포함된 기사
            
            # 날짜 추출
            date = self.extract_date(soup, url)
            
            return {
                'title': title,
                'content': content,  # 전체 본문 수집
                'date': date,
                'url': url,
                'source': 'yonhap',
                'keyword': self.keyword,
                'content_length': len(content)
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"연합뉴스 기사 추출 타임아웃 ({url})")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"연합뉴스 연결 오류 ({url}): {e}")
            return None
        except Exception as e:
            logger.error(f"연합뉴스 기사 추출 오류 ({url}): {e}")
            return None
    
    def extract_naver_news_article(self, url: str) -> Optional[Dict]:
        """네이버 뉴스 기사 추출"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 제목
            title = None
            title_elem = soup.select_one('h2.media_end_head_headline')
            if title_elem:
                title = title_elem.text.strip()
            
            # 본문
            content = ""
            content_elem = soup.select_one('article#dic_area')
            if content_elem:
                # 불필요한 요소 제거
                for elem in content_elem.select('div.vod_player_wrap, span.end_photo_org'):
                    elem.decompose()
                content = content_elem.text.strip()
            
            if not content:
                # 구형 레이아웃
                content_elem = soup.select_one('div#articleBodyContents')
                if content_elem:
                    content = content_elem.text.strip()
            
            return {
                'title': title,
                'content': content
            } if content else None
            
        except Exception as e:
            logger.error(f"네이버 뉴스 추출 오류: {e}")
            return None
    
    def crawl_yonhap_direct(self, start_date: str, end_date: str) -> List[Dict]:
        """연합뉴스 직접 검색 (2014년용) - 연합뉴스 사이트 직접 크롤링"""
        articles = []
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        logger.info(f"연합뉴스 직접 검색: {start_date} ~ {end_date}")
        
        # 2014년도 API 시도 (실패할 가능성 높지만 시도)
        current_date = start_dt
        total_articles = 0
        
        while current_date <= end_dt:
            date_str = current_date.strftime('%Y%m%d')
            daily_articles = []
            
            # 페이지네이션 처리
            page_no = 1
            
            while True:  # 페이지 제한 없음
                # 연합뉴스 API URL (2014년도 시도)
                url = 'http://ars.yna.co.kr/api/v2/search.asis'
                
                params = {
                    'callback': 'Search.SearchPreCallback',
                    'query': self.keyword,
                    'page_no': str(page_no),
                    'period': 'diy',
                    'from': date_str,
                    'to': date_str,
                    'ctype': 'A',
                    'page_size': '50',
                    'channel': 'basic_kr'
                }
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://www.yna.co.kr/'
                }
                
                try:
                    response = requests.get(url, params=params, headers=headers, timeout=20)
                    
                    if 'Search.SearchPreCallback' in response.text:
                        # JSONP 콜백 제거 및 JSON 파싱
                        import re
                        json_str = re.search(r'Search\.SearchPreCallback\((.*)\)', response.text)
                        if json_str:
                            data = json.loads(json_str.group(1))
                            results = data.get('KR_ARTICLE', {}).get('result', [])
                            
                            # 결과가 없으면 다음 날짜로
                            if not results:
                                break
                            
                            page_articles = []
                            for item in results:
                                # 날짜 확인
                                article_date = item.get('DIST_DATE', '')
                                if article_date.startswith(date_str[:8]):
                                    # URL 생성
                                    article_id = item.get('CONTENTS_ID', '')
                                    article_url = f"https://www.yna.co.kr/view/{article_id}" if article_id else ''
                                    
                                    # 본문
                                    content = item.get('TEXT_BODY', item.get('CONTENTS', ''))
                                    
                                    article = {
                                        'title': item.get('TITLE', ''),
                                        'content': content,
                                        'date': f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}",
                                        'url': article_url,
                                        'source': 'yonhap',
                                        'keyword': self.keyword,
                                        'content_length': len(content)
                                    }
                                    
                                    # API가 본문을 제공하지 않거나 너무 짧은 경우
                                    if (not article['content'] or article['content_length'] < 200) and article['url']:
                                        logger.debug(f"    콘텐츠 부족, URL 방문: {article['url']}")
                                        full_article = self.extract_yonhap_article(article['url'])
                                        if full_article and full_article.get('content'):
                                            article['content'] = full_article['content']
                                            article['content_length'] = len(full_article['content'])
                                    
                                    page_articles.append(article)
                            
                            daily_articles.extend(page_articles)
                            
                            # 이 페이지에서 날짜가 맞는 기사가 하나도 없으면 종료
                            if len(page_articles) == 0 and page_no > 1:
                                break
                            
                            # 결과가 없으면 마지막 페이지로 간주
                            if len(results) == 0:
                                break
                            
                            page_no += 1
                            time.sleep(0.3)
                    else:
                        # API 응답이 없으면 다음 날짜로
                        break
                    
                except Exception as e:
                    logger.debug(f"연합뉴스 API 오류 ({date_str}, 페이지 {page_no}): {e}")
                    break
            
            # 하루 수집 결과 정리
            if daily_articles:
                articles.extend(daily_articles)
                logger.info(f"  {current_date.strftime('%Y-%m-%d')}: {len(daily_articles)}개 수집")
                total_articles += len(daily_articles)
            
            time.sleep(0.5)
            current_date += timedelta(days=1)
        
        # API 결과가 없으면 경고
        if total_articles == 0:
            logger.warning(f"연합뉴스 2014년 데이터 수집 실패 - 빅카인즈(www.bigkinds.or.kr) 사용 권장")
        else:
            logger.info(f"연합뉴스 총 {total_articles}개 기사 수집 완료")
        
        return articles
    
    def crawl_edaily(self, start_date: str, end_date: str) -> List[Dict]:
        """이데일리 직접 크롤링 (네이버 검색 대신 이데일리 사이트 직접 접근)"""
        articles = []
        
        # 날짜 형식 변환 (YYYY-MM-DD -> YYYYMMDD)
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start = start_dt.strftime('%Y%m%d')
        end = end_dt.strftime('%Y%m%d')
        
        logger.info(f"이데일리 직접 크롤링 시작: {start_date} ~ {end_date}")
        
        # URL 템플릿 (작년 코드와 동일)
        base_url = f'https://www.edaily.co.kr/search/news/?source=total&keyword={self.keyword}&include=&exclude=&jname=&start={start}&end={end}&sort=latest&date=pick&exact=false&page='
        
        page_number = 1
        empty_page_count = 0
        
        while True:
            # 페이지 제한 없음 - 빈 페이지가 연속으로 나올 때까지 계속
                
            current_url = base_url + str(page_number)
            
            try:
                # 재시도 로직 추가
                max_retries = 3
                for retry in range(max_retries):
                    try:
                        response = self.session.get(current_url, timeout=20)  # timeout 증가
                        break
                    except requests.exceptions.Timeout:
                        if retry < max_retries - 1:
                            logger.warning(f"  페이지 {page_number} Timeout, 재시도 {retry + 1}/{max_retries - 1}")
                            time.sleep(2)  # 재시도 전 대기
                        else:
                            raise
                
                if response.status_code != 200:
                    logger.error(f"HTTP {response.status_code}")
                    break
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 뉴스 기사 추출
                news_items = soup.select('.newsbox_04')
                
                if not news_items:
                    empty_page_count += 1
                    logger.info(f"  페이지 {page_number}: 결과 없음")
                    if empty_page_count >= 3:
                        logger.info("  3페이지 연속 결과 없음, 종료")
                        last_page = page_number - 3
                        last_url = base_url + str(last_page)
                        logger.info(f"  수집 종료 - 마지막 페이지: {last_page}")
                        logger.info(f"  마지막 페이지 링크: {last_url}")
                        break
                else:
                    empty_page_count = 0
                    logger.info(f"  페이지 {page_number}: {len(news_items)}개 기사 발견")
                
                for item in news_items:
                    # 제목과 내용 추출
                    text_elem = item.select_one('.newsbox_texts')
                    if text_elem:
                        content_text = text_elem.text.strip()
                        lines = content_text.split('\n')
                        title = lines[0] if lines else ""
                        content = '\n'.join(lines[1:]) if len(lines) > 1 else ""
                        
                        # URL 추출
                        link_tag = item.find('a', href=True)
                        if link_tag:
                            url = 'https://www.edaily.co.kr' + link_tag['href']
                        else:
                            url = None
                        
                        # 날짜 추출
                        date_elem = item.select_one('.author_category')
                        if date_elem:
                            date_text = date_elem.text.split()[0]
                            # 날짜 형식 변환 (YYYY.MM.DD -> YYYY-MM-DD)
                            try:
                                date_obj = datetime.strptime(date_text, '%Y.%m.%d')
                                date_str = date_obj.strftime('%Y-%m-%d')
                                
                                # 날짜 범위 확인
                                if start_dt.date() <= date_obj.date() <= end_dt.date():
                                    # URL에서 전체 기사 내용 가져오기
                                    full_content = content  # 기본값은 미리보기
                                    if url:
                                        full_article = self.extract_edaily_article(url)
                                        if full_article and full_article.get('content'):
                                            full_content = full_article['content']
                                            logger.debug(f"    본문 수집: {len(full_content)}자")
                                    
                                    article = {
                                        'date': date_str,
                                        'title': title,
                                        'content': full_content,  # 전체 본문
                                        'url': url,
                                        'source': 'edaily',
                                        'content_length': len(full_content)
                                    }
                                    articles.append(article)
                                    logger.info(f"    ✓ {title[:50]}...")
                            except:
                                pass
                
                page_number += 1
                time.sleep(0.5)  # 서버 부하 방지
                
            except requests.exceptions.Timeout as e:
                logger.error(f"페이지 {page_number} Timeout 오류 (모든 재시도 실패): {e}")
                # Timeout 시 잠시 대기 후 다음 페이지 시도
                time.sleep(5)
                page_number += 1
                continue
                
            except requests.exceptions.ConnectionError as e:
                logger.error(f"페이지 {page_number} 연결 오류: {e}")
                time.sleep(5)
                page_number += 1
                continue
                
            except Exception as e:
                logger.error(f"페이지 {page_number} 기타 오류: {e}")
                break
        
        logger.info(f"이데일리 크롤링 완료: 총 {len(articles)}개 기사 수집")
        if page_number > 1:
            logger.info(f"  검증용 링크 - 1페이지: {base_url}1")
            logger.info(f"  검증용 링크 - 마지막 확인 페이지: {base_url}{page_number}")
        return articles
    
    def extract_edaily_article(self, url: str) -> Optional[Dict]:
        """이데일리 기사 전체 본문 추출 - 작년 검증된 코드 기반"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 본문 추출 (작년 코드 기반)
            content = ""
            content_selectors = [
                'div.news_body',      # 메인 본문 컨테이너
                'div.article_body',   # 대체 본문 컨테이너
                'div#newsContent',    # 구형 페이지
                'article'             # 최신 HTML5 구조
            ]
            
            for selector in content_selectors:
                elem = soup.select_one(selector)
                if elem:
                    # 텍스트만 추출 (작년 로직과 동일)
                    texts = elem.find_all(text=True, recursive=True)
                    content = ' '.join([t.strip() for t in texts if t.strip()])
                    if content:  # 내용이 있으면 사용
                        break
            
            return {
                'content': content if content else None
            }
            
        except Exception as e:
            logger.error(f"이데일리 기사 추출 오류 ({url}): {e}")
            return None
    
    def crawl_infomax(self, start_date: str, end_date: str) -> List[Dict]:
        """인포맥스 크롤링 (직접 사이트) - 개선된 버전"""
        articles = []
        collected_titles = set()  # 제목 기반 중복 제거 추가
        collected_urls = set()  # URL 기반 중복 제거 (함수 레벨로 이동)
        total_duplicates = 0  # 전체 중복 카운트
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        logger.info(f"인포맥스 검색: {start_date} ~ {end_date}")
        
        # 새로운 세션 생성하여 캐시 문제 방지
        import requests
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        # 인포맥스 메인 페이지 방문 (세션 초기화)
        session.get('https://news.einfomax.co.kr')
        time.sleep(0.5)
        
        # 날짜별이 아닌 전체 기간 검색으로 변경
        start_str = start_dt.strftime('%Y%m%d')
        end_str = end_dt.strftime('%Y%m%d')
        
        page = 1
        consecutive_empty = 0  # 연속 빈 페이지 카운터
        
        while True:  # 페이지 제한 없음
            url = "https://news.einfomax.co.kr/news/articleList.html"
            params = {
                'sc_word': self.keyword,
                'sc_sdate': start_str,
                'sc_edate': end_str,
                'page': str(page)
                # sc_section_code 제거 - 전체 섹션 검색
            }
            
            try:
                # 각 페이지마다 Referer 헤더 추가
                headers = {
                    'Referer': f'https://news.einfomax.co.kr/news/articleList.html?page={page-1}' if page > 1 else 'https://news.einfomax.co.kr'
                }
                response = session.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 기사 링크 찾기 - 개선된 방식
                    article_links = []
                    seen_ids = set()  # 이 페이지에서 본 기사 ID
                    
                    for a in soup.find_all('a', href=True):
                        href = a.get('href', '')
                        # 더 정확한 패턴 매칭
                        if '/articleView.html?idxno=' in href:
                            # 기사 ID 추출
                            try:
                                article_id = href.split('idxno=')[1].split('&')[0]
                                
                                # 이 페이지에서 중복 제거
                                if article_id not in seen_ids:
                                    seen_ids.add(article_id)
                                    
                                    if not href.startswith('http'):
                                        href = urljoin('https://news.einfomax.co.kr', href)
                                    
                                    url_hash = hashlib.md5(href.encode()).hexdigest()
                                    if url_hash not in collected_urls:
                                        collected_urls.add(url_hash)
                                        article_links.append(href)
                            except:
                                pass
                    
                    if not article_links:
                        consecutive_empty += 1
                        logger.info(f"  페이지 {page}: 결과 없음")
                        if consecutive_empty >= 5:  # 연속 5페이지 빈 경우 종료 (더 관대하게)
                            logger.info("  연속 5페이지 빈 결과, 크롤링 종료")
                            last_page = page - 5
                            base_search_url = f'https://news.einfomax.co.kr/news/articleList.html?page={last_page}&sc_section_code=&sc_sub_section_code=&sc_serial_code=&sc_area=&sc_level=&sc_article_type=&sc_view_level=&sc_sdate={start_str}&sc_edate={end_str}&sc_serial_number=&sc_word={quote(self.keyword)}'
                            logger.info(f"  수집 종료 - 마지막 페이지: {last_page}")
                            logger.info(f"  마지막 페이지 링크: {base_search_url}")
                            break
                    else:
                        consecutive_empty = 0  # 리셋
                        logger.info(f"  페이지 {page}: {len(article_links)}개 발견")
                    
                    # 각 링크에서 기사 추출 (page 증가 전에 처리)
                    page_articles_count = 0
                    duplicate_count = 0
                    date_filtered_count = 0
                    
                    for link in article_links:
                        article = self.extract_infomax_article(link, session=session)
                        if article:
                            # 제목 기반 중복 체크 추가
                            title_hash = hashlib.md5(article['title'].encode()).hexdigest()
                            if title_hash not in collected_titles:
                                collected_titles.add(title_hash)
                                
                                # 날짜 확인
                                article_date = None
                                if article.get('date'):
                                    try:
                                        article_date = datetime.strptime(article['date'], '%Y-%m-%d')
                                        # 날짜가 범위 내인지 확인
                                        if start_dt.date() <= article_date.date() <= end_dt.date():
                                            articles.append(article)
                                            logger.info(f"    ✓ {article['title'][:50]}...")
                                            page_articles_count += 1
                                        else:
                                            date_filtered_count += 1
                                            logger.debug(f"    ⚠️ 날짜 범위 제외: {article['title'][:30]}... [{article_date.strftime('%Y-%m-%d')}]")
                                    except:
                                        # 날짜 파싱 실패 시 포함
                                        articles.append(article)
                                        logger.info(f"    ✓ {article['title'][:50]}...")
                                        page_articles_count += 1
                            else:
                                duplicate_count += 1
                                total_duplicates += 1
                    
                    # 해당 페이지 처리 결과 상세 로깅
                    if page_articles_count > 0 or duplicate_count > 0 or date_filtered_count > 0:
                        status_parts = []
                        if page_articles_count > 0:
                            status_parts.append(f"{page_articles_count}개 수집")
                        if duplicate_count > 0:
                            status_parts.append(f"{duplicate_count}개 중복")
                        if date_filtered_count > 0:
                            status_parts.append(f"{date_filtered_count}개 날짜범위 제외")
                        logger.info(f"    → 페이지 {page} 결과: {', '.join(status_parts)}")
                    
                    # 페이지 증가는 기사 추출 완료 후에
                    page += 1
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"인포맥스 검색 오류: {e}")
                break
        
        logger.info(f"인포맥스 크롤링 완료: 총 {len(articles)}개 기사 수집 (중복 {total_duplicates}개 제외)")
        if page > 1:
            first_url = f'https://news.einfomax.co.kr/news/articleList.html?page=1&sc_section_code=&sc_sub_section_code=&sc_serial_code=&sc_area=&sc_level=&sc_article_type=&sc_view_level=&sc_sdate={start_str}&sc_edate={end_str}&sc_serial_number=&sc_word={quote(self.keyword)}'
            last_url = f'https://news.einfomax.co.kr/news/articleList.html?page={page}&sc_section_code=&sc_sub_section_code=&sc_serial_code=&sc_area=&sc_level=&sc_article_type=&sc_view_level=&sc_sdate={start_str}&sc_edate={end_str}&sc_serial_number=&sc_word={quote(self.keyword)}'
            logger.info(f"  검증용 링크 - 1페이지: {first_url}")
            logger.info(f"  검증용 링크 - 마지막 확인 페이지: {last_url}")
            logger.info(f"  실제 발견 기사: {len(articles) + total_duplicates}개 (수집 {len(articles)}개 + 중복 {total_duplicates}개)")
        return articles
    
    def extract_infomax_article(self, url: str, session=None) -> Optional[Dict]:
        """인포맥스 기사 추출"""
        try:
            # 세션이 제공되지 않으면 기본 세션 사용
            if session is None:
                session = self.session
            response = session.get(url, timeout=10)
            
            if response.status_code != 200:
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
            
            # 키워드 확인 제거 - 이미 검색 결과에 포함된 기사들
            
            # 날짜 추출 - 두 번째 li 요소에 날짜 있음
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
                'content': content,  # 전체 본문 수집
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
        
        # 정규화
        date_str = date_str.strip()
        
        # 패턴들
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
                        # YYYYMMDD 형식
                        date_val = groups[0]
                        return f"{date_val[:4]}-{date_val[4:6]}-{date_val[6:8]}"
                    else:
                        year, month, day = groups[:3]
                        return f"{year}-{int(month):02d}-{int(day):02d}"
                except:
                    continue
        
        return None
    
    def crawl_all(self, start_date: str, end_date: str, sources=['yonhap', 'edaily', 'infomax']) -> Dict[str, List[Dict]]:
        """모든 소스에서 크롤링"""
        results = {}
        
        if 'yonhap' in sources:
            logger.info("\n=== 연합뉴스 크롤링 시작 ===")
            yonhap_articles = self.crawl_yonhap(start_date, end_date)
            results['yonhap'] = yonhap_articles
            logger.info(f"연합뉴스: {len(yonhap_articles)}개 수집")
        
        if 'edaily' in sources:
            logger.info("\n=== 이데일리 크롤링 시작 ===")
            edaily_articles = self.crawl_edaily(start_date, end_date)
            results['edaily'] = edaily_articles
            logger.info(f"이데일리: {len(edaily_articles)}개 수집")
        
        if 'infomax' in sources:
            logger.info("\n=== 인포맥스 크롤링 시작 ===")
            infomax_articles = self.crawl_infomax(start_date, end_date)
            results['infomax'] = infomax_articles
            logger.info(f"인포맥스: {len(infomax_articles)}개 수집")
        
        return results
    
    def save_to_json(self, data: Dict, filename: str):
        """JSON 파일로 저장"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        total_articles = sum(len(articles) for articles in data.values())
        logger.info(f"저장 완료: {filename} (총 {total_articles}개)")


def main():
    """테스트 실행"""
    crawler = UnifiedNewsCrawler(keyword="금리")
    
    # 2015년 1월 테스트
    print("\n" + "="*60)
    print("2015년 1월 데이터 수집 테스트")
    print("="*60)
    
    results_2015 = crawler.crawl_all('2015-01-01', '2015-01-07')
    
    print("\n수집 결과:")
    for source, articles in results_2015.items():
        print(f"  {source}: {len(articles)}개")
        if articles:
            print(f"    샘플: {articles[0]['title'][:50]}...")
    
    # 저장
    crawler.save_to_json(results_2015, '/tmp/unified_2015_test.json')
    
    # 2020년 1월 테스트
    print("\n" + "="*60)
    print("2020년 1월 데이터 수집 테스트")
    print("="*60)
    
    results_2020 = crawler.crawl_all('2020-01-01', '2020-01-07')
    
    print("\n수집 결과:")
    for source, articles in results_2020.items():
        print(f"  {source}: {len(articles)}개")
        if articles:
            print(f"    샘플: {articles[0]['title'][:50]}...")
    
    # 저장
    crawler.save_to_json(results_2020, '/tmp/unified_2020_test.json')


if __name__ == "__main__":
    main()