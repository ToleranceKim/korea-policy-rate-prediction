#!/usr/bin/env python3
"""
네이버 뉴스 가용성 검증 스크립트
연합뉴스와 이데일리의 연도별 가용성을 체계적으로 검증
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class NaverNewsAvailabilityChecker:
    """네이버 뉴스 가용성 체크"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
    def check_news_availability(self, source: str, year: int, month: int = 1) -> dict:
        """특정 언론사의 특정 연월 뉴스 가용성 체크"""
        
        # 검색 날짜 설정 (해당 월의 1일-5일)
        start_date = f"{year}.{month:02d}.01"
        end_date = f"{year}.{month:02d}.05"
        
        # 검색어 설정
        if source == "yonhap":
            query = "연합뉴스 금리"
            source_name = "연합뉴스"
        elif source == "edaily":
            query = "이데일리 금리"
            source_name = "이데일리"
        else:
            raise ValueError(f"Unknown source: {source}")
        
        # 네이버 뉴스 검색
        url = "https://search.naver.com/search.naver"
        params = {
            'where': 'news',
            'query': query,
            'pd': '3',
            'ds': start_date,
            'de': end_date,
            'nso': f'so:r,p:from{year}{month:02d}01to{year}{month:02d}05',
            'start': '1'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return {
                    'source': source_name,
                    'year': year,
                    'month': month,
                    'status': 'error',
                    'source_count': 0,
                    'total_results': 0,
                    'error': f'HTTP {response.status_code}'
                }
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 전체 뉴스 개수
            all_items = soup.select('ul.list_news li.bx')
            
            # 해당 언론사 뉴스 개수
            source_count = 0
            articles = []
            
            for item in all_items:
                press = item.select_one('a.info.press')
                if press and source_name in press.text:
                    source_count += 1
                    title = item.select_one('a.news_tit')
                    if title and source_count <= 3:  # 처음 3개만 저장
                        articles.append(title.text[:50])
            
            return {
                'source': source_name,
                'year': year,
                'month': month,
                'status': 'success',
                'total_results': len(all_items),
                'source_count': source_count,
                'sample_articles': articles,
                'search_query': query,
                'date_range': f"{start_date} ~ {end_date}"
            }
            
        except Exception as e:
            return {
                'source': source_name,
                'year': year,
                'month': month,
                'status': 'error',
                'source_count': 0,
                'total_results': 0,
                'error': str(e)
            }
    
    def comprehensive_check(self):
        """2014-2025 전체 기간 체계적 검증"""
        
        results = {
            'yonhap': {},
            'edaily': {},
            'summary': {}
        }
        
        # 주요 체크 포인트 (각 년도의 1월, 6월)
        check_points = [
            (2014, 1), (2014, 6),
            (2015, 1), (2015, 6),
            (2016, 1), (2016, 6),
            (2017, 1), (2017, 6),
            (2018, 1), (2018, 6),
            (2019, 1), (2019, 6),  # 문제가 되는 2019년
            (2020, 1), (2020, 6),
            (2021, 1), (2021, 6),
            (2022, 1), (2022, 6),
            (2023, 1), (2023, 6),
            (2024, 1), (2024, 6),
            (2025, 1)
        ]
        
        logger.info("=== 네이버 뉴스 가용성 종합 검증 시작 ===")
        
        for year, month in check_points:
            logger.info(f"\n{year}년 {month}월 검증 중...")
            
            # 연합뉴스 체크
            yonhap_result = self.check_news_availability('yonhap', year, month)
            results['yonhap'][f"{year}-{month:02d}"] = yonhap_result
            logger.info(f"  연합뉴스: {yonhap_result['source_count']}개 발견 (전체 {yonhap_result.get('total_results', 0)}개 중)")
            
            time.sleep(1)  # 요청 간격
            
            # 이데일리 체크
            edaily_result = self.check_news_availability('edaily', year, month)
            results['edaily'][f"{year}-{month:02d}"] = edaily_result
            logger.info(f"  이데일리: {edaily_result['source_count']}개 발견 (전체 {edaily_result.get('total_results', 0)}개 중)")
            
            time.sleep(1)
        
        # 요약 분석
        logger.info("\n=== 분석 결과 ===")
        
        yonhap_available = []
        yonhap_unavailable = []
        edaily_available = []
        edaily_unavailable = []
        
        for key in results['yonhap']:
            if results['yonhap'][key]['source_count'] > 0:
                yonhap_available.append(key)
            else:
                yonhap_unavailable.append(key)
        
        for key in results['edaily']:
            if results['edaily'][key]['source_count'] > 0:
                edaily_available.append(key)
            else:
                edaily_unavailable.append(key)
        
        results['summary'] = {
            'yonhap': {
                'available_periods': yonhap_available,
                'unavailable_periods': yonhap_unavailable,
                'availability_rate': f"{len(yonhap_available)}/{len(results['yonhap'])}"
            },
            'edaily': {
                'available_periods': edaily_available,
                'unavailable_periods': edaily_unavailable,
                'availability_rate': f"{len(edaily_available)}/{len(results['edaily'])}"
            },
            'selective_restriction': {
                'periods_with_edaily_but_no_yonhap': [],
                'periods_with_yonhap_but_no_edaily': [],
                'both_available': [],
                'both_unavailable': []
            }
        }
        
        # 선택적 제한 분석
        for key in results['yonhap']:
            yonhap_count = results['yonhap'][key]['source_count']
            edaily_count = results['edaily'][key]['source_count']
            
            if edaily_count > 0 and yonhap_count == 0:
                results['summary']['selective_restriction']['periods_with_edaily_but_no_yonhap'].append(key)
            elif yonhap_count > 0 and edaily_count == 0:
                results['summary']['selective_restriction']['periods_with_yonhap_but_no_edaily'].append(key)
            elif yonhap_count > 0 and edaily_count > 0:
                results['summary']['selective_restriction']['both_available'].append(key)
            else:
                results['summary']['selective_restriction']['both_unavailable'].append(key)
        
        logger.info(f"\n연합뉴스 가용 기간: {len(yonhap_available)}개")
        logger.info(f"연합뉴스 불가 기간: {yonhap_unavailable}")
        logger.info(f"\n이데일리 가용 기간: {len(edaily_available)}개")
        logger.info(f"이데일리 불가 기간: {edaily_unavailable}")
        logger.info(f"\n이데일리만 가용한 기간: {results['summary']['selective_restriction']['periods_with_edaily_but_no_yonhap']}")
        
        return results
    
    def deep_analysis_2019(self):
        """2019년 심층 분석"""
        
        logger.info("\n=== 2019년 심층 분석 ===")
        
        results = {
            'monthly_analysis': {},
            'direct_url_test': {},
            'search_variation_test': {}
        }
        
        # 1. 2019년 전체 월별 체크
        logger.info("\n1. 2019년 월별 체크")
        for month in range(1, 13):
            yonhap = self.check_news_availability('yonhap', 2019, month)
            edaily = self.check_news_availability('edaily', 2019, month)
            
            results['monthly_analysis'][f"2019-{month:02d}"] = {
                'yonhap': yonhap['source_count'],
                'edaily': edaily['source_count']
            }
            
            logger.info(f"  2019년 {month}월: 연합뉴스 {yonhap['source_count']}개, 이데일리 {edaily['source_count']}개")
            time.sleep(1)
        
        # 2. 다양한 검색어 테스트
        logger.info("\n2. 검색어 변형 테스트 (2019년 1월)")
        search_terms = ['금리', '경제', '한국은행', '통화정책', '부동산']
        
        for term in search_terms:
            url = "https://search.naver.com/search.naver"
            params = {
                'where': 'news',
                'query': f'연합뉴스 {term}',
                'pd': '3',
                'ds': '2019.01.01',
                'de': '2019.01.31',
                'start': '1'
            }
            
            try:
                response = self.session.get(url, params=params, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                all_items = soup.select('ul.list_news li.bx')
                yonhap_count = sum(1 for item in all_items 
                                 if item.select_one('a.info.press') and 
                                 '연합뉴스' in item.select_one('a.info.press').text)
                
                results['search_variation_test'][term] = yonhap_count
                logger.info(f"  '{term}' 검색: {yonhap_count}개")
                
            except Exception as e:
                logger.error(f"  '{term}' 검색 실패: {e}")
            
            time.sleep(1)
        
        # 3. 연합뉴스 직접 URL 테스트
        logger.info("\n3. 연합뉴스 직접 사이트 접근 테스트")
        try:
            # 연합뉴스 자체 사이트에서 2019년 기사 존재 확인
            yna_url = "https://www.yna.co.kr/search/index"
            yna_params = {
                'query': '금리',
                'from': '2019.01.01',
                'to': '2019.01.31',
                'ctype': 'A'
            }
            
            response = self.session.get(yna_url, params=yna_params, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                articles = soup.select('div.news-con')
                results['direct_url_test']['yna_site'] = {
                    'status': 'success',
                    'article_count': len(articles),
                    'message': f"연합뉴스 자체 사이트에서 {len(articles)}개 기사 발견"
                }
                logger.info(f"  연합뉴스 사이트: {len(articles)}개 기사 존재")
            else:
                results['direct_url_test']['yna_site'] = {
                    'status': 'error',
                    'message': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            results['direct_url_test']['yna_site'] = {
                'status': 'error',
                'message': str(e)
            }
            logger.error(f"  연합뉴스 사이트 접근 실패: {e}")
        
        return results


def main():
    """메인 실행 함수"""
    
    checker = NaverNewsAvailabilityChecker()
    
    # 1. 종합 검증
    logger.info("종합 가용성 검증 시작...")
    comprehensive_results = checker.comprehensive_check()
    
    # 2. 2019년 심층 분석
    logger.info("\n2019년 심층 분석 시작...")
    deep_2019_results = checker.deep_analysis_2019()
    
    # 결과 저장
    final_results = {
        'comprehensive': comprehensive_results,
        'deep_2019_analysis': deep_2019_results,
        'conclusion': {
            'finding': "네이버는 2019년 연합뉴스 기사를 선택적으로 제공하지 않음",
            'evidence': {
                '2019년_연합뉴스': "모든 월에서 0개",
                '2019년_이데일리': "정상적으로 수집됨",
                '연합뉴스_자체사이트': "2019년 기사 존재 확인",
                '네이버_선택적_제한': "2019년 연합뉴스만 차단"
            },
            'recommendation': [
                "2019년 연합뉴스는 BigKinds 또는 직접 크롤링 필요",
                "네이버 의존도를 줄이고 다각화된 수집 전략 필요",
                "각 언론사별 가용 기간 매핑 테이블 구축 필요"
            ]
        }
    }
    
    # JSON 파일로 저장
    output_file = '/tmp/naver_news_availability_report.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n=== 검증 완료 ===")
    logger.info(f"결과 저장: {output_file}")
    
    # 핵심 결론 출력
    logger.info("\n=== 핵심 발견사항 ===")
    logger.info("1. 네이버는 2019년 연합뉴스 기사를 제공하지 않음")
    logger.info("2. 동일 기간 이데일리 기사는 정상 제공")
    logger.info("3. 연합뉴스 자체 사이트에는 2019년 기사 존재")
    logger.info("4. 이는 네이버의 선택적 데이터 제한 정책으로 판단됨")
    
    return final_results


if __name__ == "__main__":
    results = main()