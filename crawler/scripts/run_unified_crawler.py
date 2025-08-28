#!/usr/bin/env python3
"""
통합 뉴스 크롤러 실행 스크립트
Scrapy 없이 requests + BeautifulSoup 사용
연합뉴스, 이데일리, 인포맥스 모두 지원
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# 상위 디렉토리를 path에 추가
sys.path.append(str(Path(__file__).parent.parent))

from unified_news_crawler import UnifiedNewsCrawler

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('unified_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class UnifiedCrawlerRunner:
    """통합 크롤러 실행 관리자"""
    
    def __init__(self, base_dir=None):
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(__file__).parent.parent
        
        self.data_dir = self.base_dir / 'data' / 'unified'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.crawler = UnifiedNewsCrawler(keyword="금리")
        
    def run_monthly_batch(self, year, month, sources=['yonhap', 'edaily', 'infomax']):
        """월별 배치 실행"""
        # 월의 첫날과 마지막날 계산
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year, 12, 31)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        start_date = first_day.strftime('%Y-%m-%d')
        end_date = last_day.strftime('%Y-%m-%d')
        
        logger.info(f"\n{'='*60}")
        logger.info(f"월별 배치 시작: {year}년 {month}월")
        logger.info(f"기간: {start_date} ~ {end_date}")
        logger.info(f"대상: {', '.join(sources)}")
        logger.info(f"{'='*60}")
        
        # 크롤링 실행
        results = self.crawler.crawl_all(start_date, end_date, sources)
        
        # 결과 저장
        output_file = self.data_dir / f'news_{year}_{month:02d}.json'
        self.crawler.save_to_json(results, str(output_file))
        
        # 통계 출력
        stats = {
            'year': year,
            'month': month,
            'start_date': start_date,
            'end_date': end_date,
            'sources': {}
        }
        
        total_count = 0
        for source, articles in results.items():
            count = len(articles)
            stats['sources'][source] = {
                'count': count,
                'success': count > 0
            }
            total_count += count
            logger.info(f"  {source}: {count}개 수집")
        
        stats['total_count'] = total_count
        logger.info(f"  총계: {total_count}개 수집")
        
        # 통계 저장
        stats_file = self.data_dir / f'stats_{year}_{month:02d}.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        return stats
    
    def run_yearly_batch(self, year, sources=['yonhap', 'edaily', 'infomax']):
        """연도별 배치 실행"""
        logger.info(f"\n{'#'*60}")
        logger.info(f"{year}년 데이터 수집 시작")
        logger.info(f"대상: {', '.join(sources)}")
        logger.info(f"{'#'*60}")
        
        yearly_stats = []
        yearly_totals = {source: 0 for source in sources}
        yearly_totals['total'] = 0
        
        for month in range(1, 13):
            logger.info(f"\n{month}월 수집 시작...")
            
            stats = self.run_monthly_batch(year, month, sources)
            yearly_stats.append(stats)
            
            # 통계 누적
            for source in sources:
                if source in stats['sources']:
                    yearly_totals[source] += stats['sources'][source]['count']
            yearly_totals['total'] += stats['total_count']
            
            # 월간 휴지 시간 (서버 부하 방지)
            if month < 12:
                logger.info("다음 월 수집 전 30초 대기...")
                time.sleep(30)
        
        # 연간 요약 저장
        summary = {
            'year': year,
            'sources': sources,
            'totals': yearly_totals,
            'monthly_stats': yearly_stats
        }
        
        summary_file = self.data_dir / f'summary_{year}.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n{'#'*60}")
        logger.info(f"{year}년 수집 완료")
        for source in sources:
            logger.info(f"  {source}: {yearly_totals[source]}개")
        logger.info(f"  전체: {yearly_totals['total']}개")
        logger.info(f"  요약 파일: {summary_file}")
        logger.info(f"{'#'*60}")
        
        return summary
    
    def run_range_batch(self, start_year, end_year, sources=['yonhap', 'edaily', 'infomax']):
        """기간 범위 배치 실행"""
        logger.info(f"\n{'*'*70}")
        logger.info(f"대량 수집: {start_year}년 ~ {end_year}년")
        logger.info(f"대상: {', '.join(sources)}")
        logger.info(f"{'*'*70}")
        
        start_time = datetime.now()
        all_summaries = []
        
        for year in range(start_year, end_year + 1):
            summary = self.run_yearly_batch(year, sources)
            all_summaries.append(summary)
            
            # 연도간 휴지 시간
            if year < end_year:
                logger.info(f"\n다음 연도 수집 전 60초 대기...")
                time.sleep(60)
        
        # 전체 요약
        elapsed_time = datetime.now() - start_time
        total_articles = sum(s['totals']['total'] for s in all_summaries)
        
        final_summary = {
            'start_year': start_year,
            'end_year': end_year,
            'sources': sources,
            'total_articles': total_articles,
            'elapsed_time': str(elapsed_time),
            'yearly_summaries': all_summaries
        }
        
        final_file = self.data_dir / f'final_summary_{start_year}_{end_year}.json'
        with open(final_file, 'w', encoding='utf-8') as f:
            json.dump(final_summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n{'*'*70}")
        logger.info(f"전체 수집 완료")
        logger.info(f"  기간: {start_year}년 ~ {end_year}년")
        logger.info(f"  총 기사: {total_articles:,}개")
        logger.info(f"  소요 시간: {elapsed_time}")
        logger.info(f"  최종 요약: {final_file}")
        logger.info(f"{'*'*70}")
        
        return final_summary
    
    def merge_data_files(self, pattern='news_*.json'):
        """데이터 파일 병합"""
        logger.info("\n데이터 파일 병합 시작...")
        
        all_articles = {
            'yonhap': [],
            'edaily': [],
            'infomax': []
        }
        
        json_files = list(self.data_dir.glob(pattern))
        
        for json_file in sorted(json_files):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    for source in ['yonhap', 'edaily', 'infomax']:
                        if source in data:
                            all_articles[source].extend(data[source])
                            logger.info(f"  {json_file.name} - {source}: {len(data[source])}개")
                            
            except Exception as e:
                logger.error(f"파일 읽기 실패: {json_file.name} - {e}")
        
        # 각 소스별 중복 제거 및 정렬
        for source in all_articles:
            # 중복 제거 (URL 기준)
            unique_articles = []
            seen_urls = set()
            
            for article in all_articles[source]:
                url = article.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_articles.append(article)
            
            # 날짜순 정렬
            unique_articles.sort(key=lambda x: x.get('date', ''))
            all_articles[source] = unique_articles
            
            logger.info(f"{source}: 중복 제거 후 {len(unique_articles)}개")
        
        # 병합 파일 저장
        merged_file = self.data_dir / f'merged_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(merged_file, 'w', encoding='utf-8') as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=2)
        
        total_count = sum(len(articles) for articles in all_articles.values())
        
        logger.info(f"\n병합 완료:")
        logger.info(f"  연합뉴스: {len(all_articles['yonhap'])}개")
        logger.info(f"  이데일리: {len(all_articles['edaily'])}개")
        logger.info(f"  인포맥스: {len(all_articles['infomax'])}개")
        logger.info(f"  전체: {total_count}개")
        logger.info(f"  저장 파일: {merged_file}")
        
        return merged_file
    
    def test_crawling(self):
        """크롤링 테스트 (최근 1주일)"""
        logger.info("\n크롤링 테스트 시작 (최근 1주일)...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        results = self.crawler.crawl_all(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
            sources=['yonhap', 'edaily', 'infomax']
        )
        
        logger.info("\n테스트 결과:")
        for source, articles in results.items():
            logger.info(f"  {source}: {len(articles)}개")
            if articles:
                logger.info(f"    최신 기사: {articles[0]['title'][:50]}...")
        
        test_file = self.data_dir / f'test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        self.crawler.save_to_json(results, str(test_file))
        
        return results


def main():
    """메인 실행 함수"""
    runner = UnifiedCrawlerRunner()
    
    # 명령행 인자 처리
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'test':
            # 테스트: python run_unified_crawler.py test
            runner.test_crawling()
            
        elif command == 'monthly' and len(sys.argv) >= 4:
            # 월별 실행: python run_unified_crawler.py monthly 2020 1
            year = int(sys.argv[2])
            month = int(sys.argv[3])
            
            # 선택적으로 소스 지정
            if len(sys.argv) > 4:
                sources = sys.argv[4].split(',')
            else:
                sources = ['yonhap', 'edaily', 'infomax']
            
            runner.run_monthly_batch(year, month, sources)
            
        elif command == 'yearly' and len(sys.argv) >= 3:
            # 연도별 실행: python run_unified_crawler.py yearly 2020
            year = int(sys.argv[2])
            
            # 선택적으로 소스 지정
            if len(sys.argv) > 3:
                sources = sys.argv[3].split(',')
            else:
                sources = ['yonhap', 'edaily', 'infomax']
            
            runner.run_yearly_batch(year, sources)
            
        elif command == 'range' and len(sys.argv) >= 4:
            # 범위 실행: python run_unified_crawler.py range 2015 2025
            start_year = int(sys.argv[2])
            end_year = int(sys.argv[3])
            
            # 선택적으로 소스 지정
            if len(sys.argv) > 4:
                sources = sys.argv[4].split(',')
            else:
                sources = ['yonhap', 'edaily', 'infomax']
            
            runner.run_range_batch(start_year, end_year, sources)
            
        elif command == 'merge':
            # 데이터 병합: python run_unified_crawler.py merge
            runner.merge_data_files()
            
        else:
            print("사용법:")
            print("  테스트: python run_unified_crawler.py test")
            print("  월별 실행: python run_unified_crawler.py monthly <year> <month> [sources]")
            print("  연도별 실행: python run_unified_crawler.py yearly <year> [sources]")
            print("  범위 실행: python run_unified_crawler.py range <start_year> <end_year> [sources]")
            print("  데이터 병합: python run_unified_crawler.py merge")
            print("")
            print("sources 예시: yonhap,edaily,infomax (쉼표로 구분)")
            
    else:
        # 기본 실행: 테스트
        print("기본 실행: 최근 1주일 테스트")
        runner.test_crawling()


if __name__ == "__main__":
    main()