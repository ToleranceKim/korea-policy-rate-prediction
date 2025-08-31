#!/usr/bin/env python3
"""
빅카인즈(BigKinds) API 크롤러
공식 API를 사용한 뉴스 데이터 수집
"""
import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class BigKindsCrawler:
    """빅카인즈 공식 API 크롤러"""
    
    def __init__(self, api_key: str = None):
        """
        초기화
        
        Args:
            api_key: 빅카인즈 API 키 (없으면 환경변수에서 읽음)
        """
        self.api_key = api_key or os.getenv('BIGKINDS_API_KEY')
        if not self.api_key:
            logger.warning("API 키가 없습니다. 빅카인즈에서 API를 신청하세요.")
            logger.warning("신청: https://www.bigkinds.or.kr")
        
        # API 엔드포인트
        self.base_url = "https://www.bigkinds.or.kr/api/news"
        
        # 세션 설정
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; BigKindsCrawler/1.0)',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        
        if self.api_key:
            self.session.headers['X-API-KEY'] = self.api_key
    
    def search_news(self, 
                   query: str,
                   start_date: str, 
                   end_date: str,
                   providers: List[str] = None,
                   max_results: int = 1000) -> List[Dict]:
        """
        뉴스 검색
        
        Args:
            query: 검색어
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            providers: 언론사 리스트 ['연합뉴스', '이데일리', '연합인포맥스']
            max_results: 최대 결과 수
        
        Returns:
            뉴스 기사 리스트
        """
        if not self.api_key:
            logger.error("API 키가 필요합니다")
            return []
        
        articles = []
        page = 1
        
        # 날짜 형식 변환
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        logger.info(f"빅카인즈 검색: {query}, {start_date} ~ {end_date}")
        
        while len(articles) < max_results:
            # API 요청 파라미터
            params = {
                'query': query,
                'startDate': start_dt.strftime('%Y%m%d'),
                'endDate': end_dt.strftime('%Y%m%d'),
                'page': page,
                'size': 100,  # 페이지당 100개
                'sort': 'date',  # 날짜순 정렬
            }
            
            # 언론사 필터
            if providers:
                params['providers'] = ','.join(providers)
            
            try:
                # API 호출
                response = self.session.get(
                    f"{self.base_url}/search",
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 결과 파싱
                    if 'documents' in data:
                        docs = data['documents']
                        
                        if not docs:
                            logger.info(f"  페이지 {page}: 더 이상 결과 없음")
                            break
                        
                        for doc in docs:
                            article = self.parse_article(doc)
                            if article:
                                articles.append(article)
                        
                        logger.info(f"  페이지 {page}: {len(docs)}개 수집 (누적: {len(articles)}개)")
                        
                        # 다음 페이지
                        if len(docs) < 100:  # 마지막 페이지
                            break
                        
                        page += 1
                        time.sleep(1)  # API 호출 간격
                    else:
                        logger.warning("응답에 documents가 없습니다")
                        break
                        
                elif response.status_code == 429:
                    logger.warning("Rate limit 초과. 60초 대기...")
                    time.sleep(60)
                    
                elif response.status_code == 401:
                    logger.error("API 키 인증 실패")
                    break
                    
                else:
                    logger.error(f"API 오류: {response.status_code}")
                    break
                    
            except Exception as e:
                logger.error(f"검색 오류: {e}")
                break
        
        return articles[:max_results]
    
    def parse_article(self, doc: Dict) -> Optional[Dict]:
        """
        API 응답을 기사 형식으로 파싱
        
        Args:
            doc: API 응답 문서
        
        Returns:
            파싱된 기사 딕셔너리
        """
        try:
            # 날짜 파싱
            date_str = doc.get('date', '')
            if date_str:
                # YYYYMMDD -> YYYY-MM-DD
                date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            else:
                date = None
            
            return {
                'title': doc.get('title', '').strip(),
                'content': doc.get('content', '').strip(),
                'date': date,
                'url': doc.get('url', ''),
                'source': doc.get('provider', ''),
                'author': doc.get('byline', ''),
                'category': doc.get('category', ''),
                'keyword': '금리',  # 검색 키워드
                'content_length': len(doc.get('content', ''))
            }
            
        except Exception as e:
            logger.error(f"기사 파싱 오류: {e}")
            return None
    
    def crawl_period(self,
                    query: str,
                    start_date: str,
                    end_date: str,
                    providers: List[str] = None) -> Dict[str, List[Dict]]:
        """
        기간별 크롤링
        
        Args:
            query: 검색어
            start_date: 시작 날짜
            end_date: 종료 날짜  
            providers: 언론사 리스트
        
        Returns:
            언론사별 기사 딕셔너리
        """
        # 기본 언론사 설정
        if not providers:
            providers = ['연합뉴스', '이데일리', '연합인포맥스']
        
        results = {}
        
        for provider in providers:
            logger.info(f"\n{provider} 크롤링 시작...")
            
            articles = self.search_news(
                query=query,
                start_date=start_date,
                end_date=end_date,
                providers=[provider]
            )
            
            # 소스명 정규화
            source_map = {
                '연합뉴스': 'yonhap',
                '이데일리': 'edaily',
                '연합인포맥스': 'infomax'
            }
            
            source_key = source_map.get(provider, provider.lower())
            results[source_key] = articles
            
            logger.info(f"{provider}: {len(articles)}개 수집 완료")
            
            # 언론사 간 대기
            time.sleep(2)
        
        return results
    
    def save_to_json(self, data: Dict, filename: str):
        """JSON 파일로 저장"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        total_articles = sum(len(articles) for articles in data.values())
        logger.info(f"저장 완료: {filename} (총 {total_articles}개)")


class BigKindsLabCrawler:
    """빅카인즈 Lab API 크롤러 (분석 API)"""
    
    def __init__(self):
        """초기화"""
        self.session = requests.Session()
        
        # BigKinds Lab API 엔드포인트 (공개 API)
        self.endpoints = {
            'keyword': 'http://api.bigkindslab.or.kr:5002/get_keyword',
            'summary': 'http://api.bigkindslab.or.kr:5002/get_summary',
            'ner': 'http://api2.bigkindslab.or.kr:5002/get_ner',
            'classify': 'http://api2.bigkindslab.or.kr:5002/get_cls',
            'tag': 'http://api.bigkindslab.or.kr:5002/get_tag'
        }
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        텍스트에서 키워드 추출
        
        Args:
            text: 분석할 텍스트
        
        Returns:
            키워드 리스트
        """
        try:
            response = self.session.post(
                self.endpoints['keyword'],
                json={'text': text},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('keywords', [])
            
        except Exception as e:
            logger.error(f"키워드 추출 오류: {e}")
        
        return []
    
    def summarize(self, text: str) -> str:
        """
        텍스트 요약
        
        Args:
            text: 요약할 텍스트
        
        Returns:
            요약된 텍스트
        """
        try:
            response = self.session.post(
                self.endpoints['summary'],
                json={'text': text},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('summary', '')
            
        except Exception as e:
            logger.error(f"요약 오류: {e}")
        
        return ""


def main():
    """테스트 실행"""
    
    # API 키 확인
    api_key = os.getenv('BIGKINDS_API_KEY')
    
    if api_key:
        # 공식 API 사용
        crawler = BigKindsCrawler(api_key)
        
        results = crawler.crawl_period(
            query="금리",
            start_date="2024-01-01",
            end_date="2024-01-31",
            providers=['연합뉴스', '이데일리']
        )
        
        crawler.save_to_json(results, '/tmp/bigkinds_test.json')
        
    else:
        print("\n" + "="*60)
        print("빅카인즈 API 키가 없습니다!")
        print("="*60)
        print("\n1. 빅카인즈 가입: https://www.bigkinds.or.kr")
        print("2. API 신청")
        print("3. 환경변수 설정:")
        print("   export BIGKINDS_API_KEY='your-api-key'")
        print("\n또는 수동 다운로드:")
        print("1. 빅카인즈 웹사이트에서 검색")
        print("2. 엑셀 다운로드")
        print("3. JSON으로 변환")
    
    # Lab API 테스트 (공개 API)
    print("\n빅카인즈 Lab API 테스트 (공개)...")
    lab = BigKindsLabCrawler()
    
    sample_text = "한국은행이 기준금리를 인상했다. 물가 상승 압력이 지속되고 있기 때문이다."
    keywords = lab.extract_keywords(sample_text)
    summary = lab.summarize(sample_text)
    
    print(f"키워드: {keywords}")
    print(f"요약: {summary}")


if __name__ == "__main__":
    main()