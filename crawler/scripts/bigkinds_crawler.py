#!/usr/bin/env python3
"""
BigKinds API를 활용한 뉴스 크롤링
한국언론진흥재단 제공 서비스 활용
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BigKindsCrawler:
    """BigKinds 뉴스 크롤러"""
    
    def __init__(self, keyword="금리"):
        self.keyword = keyword
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
            'Referer': 'https://www.bigkinds.or.kr/'
        })
        self.collected_urls = set()
        
    def search_news(self, start_date: str, end_date: str, provider: str = None) -> List[Dict]:
        """BigKinds에서 뉴스 검색"""
        
        articles = []
        
        # 날짜 형식 변환 (YYYY-MM-DD -> YYYY.MM.DD)
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_formatted = start_dt.strftime('%Y.%m.%d')
        end_formatted = end_dt.strftime('%Y.%m.%d')
        
        logger.info(f"BigKinds 검색: {start_formatted} ~ {end_formatted}, 키워드: {self.keyword}")
        
        # BigKinds 검색 URL (실제 서비스 URL)
        search_url = 'https://www.bigkinds.or.kr/api/news/search.do'
        
        # 검색 파라미터
        params = {
            'indexName': 'news',
            'searchKey': self.keyword,
            'searchKeys': [{}],
            'byLine': '',
            'searchFilterType': '1',
            'searchSortType': 'date',
            'sortMethod': 'desc',
            'mainTodayPersonYn': '',
            'startDate': start_formatted,
            'endDate': end_formatted,
            'newsIds': [],
            'categoryCodes': [],
            'providerCodes': [],
            'incidentCodes': [],
            'networkNodeType': '',
            'topicOrigin': '',
            'startNo': 1,
            'resultNumber': 100
        }
        
        # 특정 언론사 필터링
        if provider:
            if provider.lower() in ['yonhap', '연합뉴스']:
                params['providerCodes'] = ['01100001']  # 연합뉴스 코드
            elif provider.lower() in ['edaily', '이데일리']:
                params['providerCodes'] = ['01100901']  # 이데일리 코드
        
        try:
            # 세션 초기화 (쿠키 획득)
            main_resp = self.session.get('https://www.bigkinds.or.kr/')
            
            # 검색 요청
            response = self.session.post(
                search_url,
                json=params,
                headers={'Content-Type': 'application/json;charset=UTF-8'}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'resultList' in data:
                    news_list = data['resultList']
                    total_count = data.get('totalCount', 0)
                    
                    logger.info(f"  검색 결과: {total_count}개 중 {len(news_list)}개 처리")
                    
                    for item in news_list:
                        article = self._extract_article(item)
                        if article and article['url'] not in self.collected_urls:
                            articles.append(article)
                            self.collected_urls.add(article['url'])
                            logger.info(f"    ✓ {article['title'][:40]}...")
                else:
                    logger.warning("검색 결과가 없습니다.")
            else:
                logger.error(f"API 요청 실패: {response.status_code}")
                
        except Exception as e:
            logger.error(f"BigKinds 검색 오류: {e}")
        
        return articles
    
    def _extract_article(self, item: Dict) -> Optional[Dict]:
        """기사 정보 추출"""
        try:
            # BigKinds 응답 형식에 맞춰 추출
            title = item.get('TITLE', '').replace('<![CDATA[', '').replace(']]>', '')
            title = BeautifulSoup(title, 'html.parser').get_text()
            
            content = item.get('CONTENT', '').replace('<![CDATA[', '').replace(']]>', '')
            content = BeautifulSoup(content, 'html.parser').get_text()
            
            date = item.get('DATE', '')
            if date:
                # YYYYMMDD 형식을 YYYY-MM-DD로 변환
                if len(date) == 8:
                    date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
            
            url = item.get('URL', '')
            provider = item.get('PROVIDER', '')
            
            return {
                'title': title,
                'url': url,
                'date': date,
                'content_preview': content[:200] if content else '',
                'source': provider,
                'keyword': self.keyword
            }
            
        except Exception as e:
            logger.error(f"기사 추출 오류: {e}")
            return None
    
    def search_with_api(self, start_date: str, end_date: str) -> Dict:
        """BigKinds Lab API 활용 (분석 기능 포함)"""
        
        results = {
            'articles': [],
            'analysis': {}
        }
        
        # 기본 검색
        articles = self.search_news(start_date, end_date)
        results['articles'] = articles
        
        # BigKinds Lab API 엔드포인트
        api_endpoints = {
            'keyword': 'http://api.bigkindslab.or.kr:5002/get_keyword',
            'summary': 'http://api.bigkindslab.or.kr:5002/get_summary',
            'classification': 'http://api2.bigkindslab.or.kr:5002/get_cls',
            'ner': 'http://api.bigkindslab.or.kr:5002/get_tag'
        }
        
        # 분석 수행 (첫 5개 기사만)
        for article in articles[:5]:
            if article.get('content_preview'):
                try:
                    # 키워드 추출
                    keyword_resp = requests.post(
                        api_endpoints['keyword'],
                        json={'text': article['content_preview']},
                        headers={'Content-Type': 'application/json;charset=UTF-8'}
                    )
                    
                    if keyword_resp.status_code == 200:
                        keywords = keyword_resp.json()
                        article['keywords'] = keywords
                        
                except Exception as e:
                    logger.error(f"API 분석 오류: {e}")
        
        return results


def test_bigkinds():
    """BigKinds 크롤러 테스트"""
    
    crawler = BigKindsCrawler(keyword="금리")
    
    # 2019년 1월 테스트
    print("\n=== BigKinds 2019년 1월 검색 테스트 ===")
    
    # 연합뉴스 검색
    print("\n연합뉴스 검색...")
    yonhap_articles = crawler.search_news('2019-01-01', '2019-01-05', provider='yonhap')
    print(f"연합뉴스: {len(yonhap_articles)}개 수집")
    
    # 이데일리 검색
    print("\n이데일리 검색...")
    crawler.collected_urls.clear()  # URL 중복 체크 초기화
    edaily_articles = crawler.search_news('2019-01-01', '2019-01-05', provider='edaily')
    print(f"이데일리: {len(edaily_articles)}개 수집")
    
    # 전체 검색
    print("\n전체 언론사 검색...")
    crawler.collected_urls.clear()
    all_articles = crawler.search_news('2019-01-01', '2019-01-05')
    print(f"전체: {len(all_articles)}개 수집")
    
    # 결과 저장
    results = {
        'yonhap': yonhap_articles,
        'edaily': edaily_articles,
        'all': all_articles[:10],  # 전체 중 10개만 저장
        'summary': {
            'yonhap_count': len(yonhap_articles),
            'edaily_count': len(edaily_articles),
            'total_count': len(all_articles),
            'period': '2019-01-01 ~ 2019-01-05'
        }
    }
    
    output_file = '/tmp/bigkinds_test.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n결과 저장: {output_file}")
    
    return results


def test_api():
    """BigKinds Lab API 테스트"""
    
    print("\n=== BigKinds Lab API 테스트 ===")
    
    # 테스트 텍스트
    test_text = "한국은행이 기준금리를 인상하면서 시중 금리도 동반 상승할 것으로 예상된다."
    
    # API 엔드포인트
    endpoints = {
        'keyword': 'http://api.bigkindslab.or.kr:5002/get_keyword',
        'summary': 'http://api.bigkindslab.or.kr:5002/get_summary',
        'ner': 'http://api.bigkindslab.or.kr:5002/get_tag'
    }
    
    headers = {'Content-Type': 'application/json;charset=UTF-8'}
    
    for name, url in endpoints.items():
        print(f"\n{name} API 테스트...")
        try:
            response = requests.post(
                url,
                json={'text': test_text},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"  ✓ 성공: {response.json()}")
            else:
                print(f"  ✗ 실패: {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ 오류: {e}")


if __name__ == "__main__":
    # BigKinds 검색 테스트
    test_bigkinds()
    
    # API 테스트 (선택적)
    # test_api()