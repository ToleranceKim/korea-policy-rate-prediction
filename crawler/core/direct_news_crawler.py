#!/usr/bin/env python3
"""
연합뉴스와 이데일리 자체 홈페이지 직접 크롤링
네이버 의존성 없이 안정적으로 데이터 수집
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional
import re
from urllib.parse import urljoin, urlparse, parse_qs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DirectNewsCrawler:
    """언론사 직접 크롤링 통합 클래스"""
    
    def __init__(self, keyword="금리"):
        self.keyword = keyword
        self.collected_urls = set()
        
    def crawl(self, source: str, start_date: str, end_date: str) -> List[Dict]:
        """통합 크롤링 메서드"""
        if source.lower() in ['yonhap', '연합뉴스', 'yna']:
            return self.crawl_yonhap(start_date, end_date)
        elif source.lower() in ['edaily', '이데일리']:
            return self.crawl_edaily(start_date, end_date)
        else:
            raise ValueError(f"지원하지 않는 언론사: {source}")
    
    def crawl_yonhap(self, start_date: str, end_date: str) -> List[Dict]:
        """연합뉴스 직접 크롤링"""
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
            'Referer': 'https://www.yna.co.kr/'
        })
        
        articles = []
        
        # 날짜 형식 변환
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        from_date = start_dt.strftime('%Y.%m.%d')
        to_date = end_dt.strftime('%Y.%m.%d')
        
        logger.info(f"연합뉴스 직접 크롤링: {from_date} ~ {to_date}")
        
        # 메인 페이지 방문 (쿠키 획득)
        try:
            session.get('https://www.yna.co.kr/', timeout=10)
        except:
            pass
        
        page = 1
        max_pages = 50  # 최대 50페이지
        empty_pages = 0
        
        while page <= max_pages and empty_pages < 3:
            url = 'https://www.yna.co.kr/search/index'
            params = {
                'query': self.keyword,
                'period': 'custom',
                'from': from_date,
                'to': to_date,
                'ctype': 'A',  # 기사만
                'page_no': str(page),
                'page_size': '20'
            }
            
            try:
                response = session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 검색 결과 추출
                    news_items = soup.select('div.news-con')
                    
                    if not news_items:
                        empty_pages += 1
                        logger.info(f"  페이지 {page}: 결과 없음")
                    else:
                        empty_pages = 0
                        logger.info(f"  페이지 {page}: {len(news_items)}개 발견")
                        
                        for item in news_items:
                            article = self._extract_yonhap_article(item, start_dt, end_dt)
                            if article and article['url'] not in self.collected_urls:
                                articles.append(article)
                                self.collected_urls.add(article['url'])
                                logger.info(f"    ✓ {article['title'][:40]}...")
                    
                    page += 1
                    time.sleep(0.5)  # 서버 부하 방지
                    
                else:
                    logger.error(f"HTTP {response.status_code}")
                    break
                    
            except Exception as e:
                logger.error(f"페이지 {page} 오류: {e}")
                break
        
        logger.info(f"연합뉴스: 총 {len(articles)}개 수집 완료")
        return articles
    
    def _extract_yonhap_article(self, item, start_dt, end_dt) -> Optional[Dict]:
        """연합뉴스 기사 정보 추출"""
        try:
            # 제목과 링크
            title_elem = item.find('strong', class_='tit-news')
            if not title_elem:
                title_elem = item.find('a')
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            
            # URL 추출
            link_elem = item.find('a', href=True)
            if not link_elem:
                return None
            
            url = link_elem['href']
            if not url.startswith('http'):
                url = 'https://www.yna.co.kr' + url
            
            # 날짜 추출
            date_elem = item.find('span', class_='p-time')
            if not date_elem:
                date_elem = item.find('span', class_='date')
            
            date = None
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                date = self._parse_date(date_text)
            
            # URL에서 날짜 추출 시도
            if not date:
                match = re.search(r'AKR(\d{8})', url)
                if match:
                    date_str = match.group(1)
                    date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            
            # 날짜 필터링
            if date:
                try:
                    article_date = datetime.strptime(date, '%Y-%m-%d')
                    if not (start_dt.date() <= article_date.date() <= end_dt.date()):
                        return None
                except:
                    pass
            
            # 본문 미리보기
            content_elem = item.find('p', class_='lead')
            if not content_elem:
                content_elem = item.find('span', class_='lead')
            
            content = content_elem.get_text(strip=True) if content_elem else ""
            
            return {
                'title': title,
                'url': url,
                'date': date,
                'content_preview': content[:200],
                'source': 'yonhap',
                'keyword': self.keyword
            }
            
        except Exception as e:
            logger.error(f"기사 추출 오류: {e}")
            return None
    
    def crawl_edaily(self, start_date: str, end_date: str) -> List[Dict]:
        """이데일리 직접 크롤링"""
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
            'Referer': 'https://www.edaily.co.kr/'
        })
        
        articles = []
        
        # 날짜 형식 변환
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        logger.info(f"이데일리 직접 크롤링: {start_date} ~ {end_date}")
        
        # 메인 페이지 방문
        try:
            session.get('https://www.edaily.co.kr/', timeout=10)
        except:
            pass
        
        page = 1
        max_pages = 50
        
        while page <= max_pages:
            # 이데일리 검색 URL
            url = 'https://www.edaily.co.kr/search/news'
            
            params = {
                'keyword': self.keyword,
                'searchdate': f'{start_date}~{end_date}',
                'page': str(page),
                'pagesize': '20'
            }
            
            try:
                response = session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # JavaScript로 렌더링되는 경우 처리
                    # 검색 결과가 JSON으로 포함되어 있는지 확인
                    script_tags = soup.find_all('script')
                    for script in script_tags:
                        if script.string and 'searchResult' in script.string:
                            # JSON 데이터 추출
                            match = re.search(r'searchResult\s*=\s*(\[.*?\]);', script.string, re.DOTALL)
                            if match:
                                try:
                                    json_data = json.loads(match.group(1))
                                    for item in json_data:
                                        article = self._extract_edaily_article_from_json(item, start_dt, end_dt)
                                        if article and article['url'] not in self.collected_urls:
                                            articles.append(article)
                                            self.collected_urls.add(article['url'])
                                            logger.info(f"    ✓ {article['title'][:40]}...")
                                except:
                                    pass
                    
                    # HTML 파싱 시도
                    news_items = soup.select('div.newsbox')
                    if not news_items:
                        news_items = soup.select('li.clearfix')
                    if not news_items:
                        news_items = soup.select('div.news_list li')
                    
                    if news_items:
                        logger.info(f"  페이지 {page}: {len(news_items)}개 발견")
                        
                        for item in news_items:
                            article = self._extract_edaily_article(item, start_dt, end_dt)
                            if article and article['url'] not in self.collected_urls:
                                articles.append(article)
                                self.collected_urls.add(article['url'])
                                logger.info(f"    ✓ {article['title'][:40]}...")
                    else:
                        # 검색 결과 없으면 종료
                        logger.info(f"  페이지 {page}: 더 이상 결과 없음")
                        break
                    
                    page += 1
                    time.sleep(0.5)
                    
                else:
                    logger.error(f"HTTP {response.status_code}")
                    break
                    
            except Exception as e:
                logger.error(f"페이지 {page} 오류: {e}")
                break
        
        logger.info(f"이데일리: 총 {len(articles)}개 수집 완료")
        return articles
    
    def _extract_edaily_article(self, item, start_dt, end_dt) -> Optional[Dict]:
        """이데일리 기사 정보 추출 (HTML)"""
        try:
            # 제목과 링크
            title_elem = item.find('a')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            url = title_elem.get('href', '')
            
            if not url.startswith('http'):
                url = 'https://www.edaily.co.kr' + url
            
            # 날짜 추출
            date_elem = item.find('span', class_='date')
            if not date_elem:
                date_elem = item.find('span', class_='time')
            
            date = None
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                date = self._parse_date(date_text)
            
            # 날짜 필터링
            if date:
                try:
                    article_date = datetime.strptime(date, '%Y-%m-%d')
                    if not (start_dt.date() <= article_date.date() <= end_dt.date()):
                        return None
                except:
                    pass
            
            # 본문 미리보기
            content_elem = item.find('p')
            content = content_elem.get_text(strip=True) if content_elem else ""
            
            return {
                'title': title,
                'url': url,
                'date': date,
                'content_preview': content[:200],
                'source': 'edaily',
                'keyword': self.keyword
            }
            
        except Exception as e:
            logger.error(f"기사 추출 오류: {e}")
            return None
    
    def _extract_edaily_article_from_json(self, item, start_dt, end_dt) -> Optional[Dict]:
        """이데일리 기사 정보 추출 (JSON)"""
        try:
            title = item.get('title', '')
            url = item.get('url', '')
            date = item.get('date', '')
            content = item.get('content', '')
            
            if not url.startswith('http'):
                url = 'https://www.edaily.co.kr' + url
            
            # 날짜 형식 변환
            if date:
                date = self._parse_date(date)
            
            # 날짜 필터링
            if date:
                try:
                    article_date = datetime.strptime(date, '%Y-%m-%d')
                    if not (start_dt.date() <= article_date.date() <= end_dt.date()):
                        return None
                except:
                    pass
            
            return {
                'title': title,
                'url': url,
                'date': date,
                'content_preview': content[:200],
                'source': 'edaily',
                'keyword': self.keyword
            }
            
        except Exception as e:
            logger.error(f"JSON 추출 오류: {e}")
            return None
    
    def _parse_date(self, date_text: str) -> Optional[str]:
        """다양한 날짜 형식 파싱"""
        
        # 정규식 패턴들
        patterns = [
            (r'(\d{4})-(\d{2})-(\d{2})', lambda m: f"{m[1]}-{m[2]}-{m[3]}"),
            (r'(\d{4})\.(\d{2})\.(\d{2})', lambda m: f"{m[1]}-{m[2]}-{m[3]}"),
            (r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', 
             lambda m: f"{m[1]}-{int(m[2]):02d}-{int(m[3]):02d}"),
            (r'(\d{2})\.(\d{2})\.(\d{2})', 
             lambda m: f"20{m[1]}-{m[2]}-{m[3]}"),  # YY.MM.DD
        ]
        
        for pattern, formatter in patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    return formatter(match.groups())
                except:
                    continue
        
        return None


def test_crawler():
    """크롤러 테스트"""
    
    crawler = DirectNewsCrawler(keyword="금리")
    
    # 2019년 1월 테스트
    print("\n=== 2019년 1월 테스트 ===")
    
    print("연합뉴스 크롤링...")
    yonhap_articles = crawler.crawl('yonhap', '2019-01-01', '2019-01-05')
    print(f"연합뉴스: {len(yonhap_articles)}개 수집")
    
    print("\n이데일리 크롤링...")
    edaily_articles = crawler.crawl('edaily', '2019-01-01', '2019-01-05')
    print(f"이데일리: {len(edaily_articles)}개 수집")
    
    # 결과 저장
    results = {
        'yonhap': yonhap_articles,
        'edaily': edaily_articles,
        'summary': {
            'yonhap_count': len(yonhap_articles),
            'edaily_count': len(edaily_articles),
            'period': '2019-01-01 ~ 2019-01-05'
        }
    }
    
    with open('/tmp/direct_crawl_test.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n결과 저장: /tmp/direct_crawl_test.json")
    
    return results


if __name__ == "__main__":
    test_crawler()