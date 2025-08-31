#!/usr/bin/env python3
"""
통합 뉴스 크롤러 실행 스크립트
기본 모드와 안전 모드를 모두 지원하는 통합 실행 스크립트
"""

import os
import sys
import json
import time
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
import argparse

# 상위 디렉토리를 path에 추가
sys.path.append(str(Path(__file__).parent.parent))

from core.base_crawler import UnifiedNewsCrawler
from core.safe_crawler import SafeUnifiedNewsCrawler

# 로깅 설정
def setup_logging(log_file='crawler.log'):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


class CrawlerRunner:
    """통합 크롤러 실행 관리자"""
    
    def __init__(self, safe_mode=False, base_dir=None):
        self.safe_mode = safe_mode
        
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(__file__).parent.parent
        
        # 데이터 디렉토리 설정
        if safe_mode:
            self.data_dir = self.base_dir / 'data' / 'safe'
        else:
            self.data_dir = self.base_dir / 'data' / 'unified'
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 크롤러 인스턴스 생성
        if safe_mode:
            self.crawler = SafeUnifiedNewsCrawler(keyword="금리", safe_mode=True)
            self.month_wait_min = 60
            self.month_wait_max = 120
        else:
            self.crawler = UnifiedNewsCrawler(keyword="금리")
            self.month_wait_min = 30
            self.month_wait_max = 60
        
        self.logger = logging.getLogger(__name__)
    
    def run_monthly(self, year, month, sources=['yonhap', 'edaily', 'infomax']):
        """월별 크롤링 실행"""
        # 월의 첫날과 마지막날 계산
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year, 12, 31)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        start_date = first_day.strftime('%Y-%m-%d')
        end_date = last_day.strftime('%Y-%m-%d')
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"월별 크롤링: {year}년 {month}월")
        self.logger.info(f"모드: {'안전' if self.safe_mode else '일반'}")
        self.logger.info(f"기간: {start_date} ~ {end_date}")
        self.logger.info(f"대상: {', '.join(sources)}")
        self.logger.info(f"{'='*60}")
        
        # 크롤링 실행
        results = self.crawler.crawl_all(start_date, end_date, sources)
        
        # 결과 저장
        output_file = self.data_dir / f'news_{year}_{month:02d}.json'
        self.crawler.save_to_json(results, str(output_file))
        
        # 통계
        stats = {
            'year': year,
            'month': month,
            'start_date': start_date,
            'end_date': end_date,
            'safe_mode': self.safe_mode,
            'sources': {}
        }
        
        total_count = 0
        for source, articles in results.items():
            count = len(articles)
            stats['sources'][source] = count
            total_count += count
            self.logger.info(f"  {source}: {count}개")
        
        stats['total'] = total_count
        self.logger.info(f"  총계: {total_count}개")
        
        return stats
    
    def run_yearly(self, year, sources=['yonhap', 'edaily', 'infomax'], start_month=1, end_month=12):
        """연도별 크롤링 실행"""
        self.logger.info(f"\n{'#'*60}")
        self.logger.info(f"{year}년 크롤링 시작")
        self.logger.info(f"모드: {'안전' if self.safe_mode else '일반'}")
        self.logger.info(f"기간: {start_month}월 ~ {end_month}월")
        self.logger.info(f"대상: {', '.join(sources)}")
        self.logger.info(f"{'#'*60}")
        
        yearly_stats = []
        yearly_total = {source: 0 for source in sources}
        yearly_total['total'] = 0
        
        for month in range(start_month, end_month + 1):
            self.logger.info(f"\n>>> {month}월 수집 시작...")
            
            stats = self.run_monthly(year, month, sources)
            yearly_stats.append(stats)
            
            # 통계 누적
            for source in sources:
                if source in stats['sources']:
                    yearly_total[source] += stats['sources'][source]
            yearly_total['total'] += stats['total']
            
            # 월간 휴지 시간
            if month < end_month:
                if self.safe_mode:
                    wait_time = random.uniform(self.month_wait_min, self.month_wait_max)
                else:
                    wait_time = random.uniform(30, 60)
                
                self.logger.info(f"다음 월 수집 전 {wait_time:.1f}초 대기...")
                time.sleep(wait_time)
            
            # 3개월마다 추가 휴지 (안전 모드)
            if self.safe_mode and month % 3 == 0 and month < end_month:
                extra_wait = random.uniform(120, 180)
                self.logger.info(f"3개월 처리 완료, 추가 {extra_wait:.1f}초 대기...")
                time.sleep(extra_wait)
        
        # 연간 요약 저장
        summary = {
            'year': year,
            'safe_mode': self.safe_mode,
            'sources': sources,
            'totals': yearly_total,
            'monthly_stats': yearly_stats,
            'range': {'start_month': start_month, 'end_month': end_month}
        }
        
        summary_file = self.data_dir / f'summary_{year}.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"\n{'#'*60}")
        self.logger.info(f"{year}년 수집 완료")
        for source in sources:
            self.logger.info(f"  {source}: {yearly_total[source]}개")
        self.logger.info(f"  전체: {yearly_total['total']}개")
        self.logger.info(f"  요약: {summary_file}")
        self.logger.info(f"{'#'*60}")
        
        return summary
    
    def test_crawl(self, days=3):
        """테스트 크롤링 (최근 N일)"""
        self.logger.info(f"\n테스트 크롤링 (최근 {days}일, {'안전' if self.safe_mode else '일반'} 모드)")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        results = self.crawler.crawl_all(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
            sources=['yonhap', 'edaily', 'infomax']
        )
        
        self.logger.info("\n테스트 결과:")
        for source, articles in results.items():
            self.logger.info(f"  {source}: {len(articles)}개")
            if articles:
                self.logger.info(f"    샘플: {articles[0]['title'][:50]}...")
        
        test_file = self.data_dir / f'test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        self.crawler.save_to_json(results, str(test_file))
        
        return results
    
    def merge_data(self, pattern='news_*.json'):
        """데이터 파일 병합"""
        self.logger.info(f"\n데이터 병합 시작: {pattern}")
        
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
                            self.logger.info(f"  {json_file.name} - {source}: {len(data[source])}개")
            
            except Exception as e:
                self.logger.error(f"파일 읽기 실패: {json_file.name} - {e}")
        
        # 중복 제거 및 정렬
        for source in all_articles:
            # URL 기준 중복 제거
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
            
            self.logger.info(f"{source}: 중복 제거 후 {len(unique_articles)}개")
        
        # 병합 파일 저장
        merged_file = self.data_dir / f'merged_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(merged_file, 'w', encoding='utf-8') as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=2)
        
        total_count = sum(len(articles) for articles in all_articles.values())
        self.logger.info(f"\n병합 완료: 총 {total_count}개")
        self.logger.info(f"저장: {merged_file}")
        
        return merged_file


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='통합 뉴스 크롤러')
    
    # 명령어 선택
    subparsers = parser.add_subparsers(dest='command', help='실행할 명령')
    
    # test 명령
    test_parser = subparsers.add_parser('test', help='테스트 크롤링')
    test_parser.add_argument('--days', type=int, default=3, help='테스트 기간 (일)')
    
    # monthly 명령
    monthly_parser = subparsers.add_parser('monthly', help='월별 크롤링')
    monthly_parser.add_argument('year', type=int, help='연도')
    monthly_parser.add_argument('month', type=int, help='월')
    monthly_parser.add_argument('--sources', default='yonhap,edaily,infomax', help='대상 소스')
    
    # yearly 명령
    yearly_parser = subparsers.add_parser('yearly', help='연도별 크롤링')
    yearly_parser.add_argument('year', type=int, help='연도')
    yearly_parser.add_argument('--sources', default='yonhap,edaily,infomax', help='대상 소스')
    yearly_parser.add_argument('--start-month', type=int, default=1, help='시작 월')
    yearly_parser.add_argument('--end-month', type=int, default=12, help='종료 월')
    
    # resume 명령
    resume_parser = subparsers.add_parser('resume', help='크롤링 재개')
    resume_parser.add_argument('year', type=int, help='연도')
    resume_parser.add_argument('month', type=int, help='재개할 월')
    resume_parser.add_argument('--sources', default='yonhap,edaily,infomax', help='대상 소스')
    
    # merge 명령
    merge_parser = subparsers.add_parser('merge', help='데이터 병합')
    merge_parser.add_argument('--pattern', default='news_*.json', help='파일 패턴')
    
    # 공통 옵션
    parser.add_argument('--safe', action='store_true', help='안전 모드 활성화')
    parser.add_argument('--log', default='crawler.log', help='로그 파일 경로')
    
    args = parser.parse_args()
    
    # 로깅 설정
    logger = setup_logging(args.log)
    
    # 크롤러 실행기 생성
    runner = CrawlerRunner(safe_mode=args.safe)
    
    # 명령 실행
    if args.command == 'test':
        runner.test_crawl(days=args.days)
    
    elif args.command == 'monthly':
        sources = args.sources.split(',')
        runner.run_monthly(args.year, args.month, sources)
    
    elif args.command == 'yearly':
        sources = args.sources.split(',')
        runner.run_yearly(args.year, sources, args.start_month, args.end_month)
    
    elif args.command == 'resume':
        sources = args.sources.split(',')
        runner.run_yearly(args.year, sources, start_month=args.month)
    
    elif args.command == 'merge':
        runner.merge_data(pattern=args.pattern)
    
    else:
        print("\n사용법:")
        print("  python run.py test                    # 테스트 (최근 3일)")
        print("  python run.py test --safe              # 안전 모드 테스트")
        print("  python run.py monthly 2015 1          # 2015년 1월 크롤링")
        print("  python run.py yearly 2015             # 2015년 전체 크롤링")
        print("  python run.py yearly 2015 --safe      # 2015년 안전 모드")
        print("  python run.py resume 2015 7           # 2015년 7월부터 재개")
        print("  python run.py merge                   # 데이터 병합")
        print("\n옵션:")
        print("  --safe                                 # 안전 모드 (느리지만 안전)")
        print("  --sources yonhap,edaily,infomax       # 소스 지정")
        print("  --start-month N --end-month M         # 월 범위 지정")
        print("\n예시:")
        print("  python run.py yearly 2015 --safe")
        print("  python run.py monthly 2015 1 --sources yonhap,edaily")
        print("  python run.py yearly 2015 --start-month 1 --end-month 6")


if __name__ == "__main__":
    main()