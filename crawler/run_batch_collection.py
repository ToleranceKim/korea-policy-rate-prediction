#!/usr/bin/env python3
"""
월별 분할 수집 실행 스크립트 (경로 수정됨)
"""

import sys
import argparse
from pathlib import Path

# scripts/batch 디렉터리를 경로에 추가
sys.path.append(str(Path(__file__).parent / "scripts" / "batch"))

from batch_collector import BatchCollector
from data_merger import DataMerger

def main():
    parser = argparse.ArgumentParser(description='월별 분할 데이터 수집 시스템')
    parser.add_argument('--crawlers', nargs='+', 
                        choices=['yonhap', 'edaily', 'infomax', 'bond', 'interest_rates', 'call_ratings', 'mpb'],
                        default=['yonhap', 'edaily', 'infomax'],
                        help='수집할 크롤러 선택')
    parser.add_argument('--test', action='store_true', help='테스트 모드 (소량 수집)')
    parser.add_argument('--resume', type=str, help='특정 월부터 재시작 (YYYY-MM 형식)')
    parser.add_argument('--merge-only', action='store_true', help='수집 없이 병합만 실행')
    parser.add_argument('--status', action='store_true', help='현재 상태만 확인')
    parser.add_argument('--start-year', type=int, default=2015, help='수집 시작 연도 (기본값: 2015)')
    parser.add_argument('--end-year', type=int, default=2025, help='수집 종료 연도 (기본값: 2025)')
    parser.add_argument('--end-month', type=int, default=8, help='종료 연도의 마지막 월 (기본값: 8)')
    
    args = parser.parse_args()
    
    collector = BatchCollector()
    
    if args.status:
        collector.print_status()
        return
    
    if args.merge_only:
        print("🔄 Starting merge-only process...")
        merger = DataMerger()
        merger.merge_all_crawlers()
        return
    
    print(f"🚀 Starting batch collection...")
    print(f"📋 Target crawlers: {args.crawlers}")
    
    if args.test:
        print("🧪 TEST MODE: Limited collection for validation")
        # 테스트 모드에서는 최근 1개월만 수집
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # 테스트용 수동 수집
        for crawler_name in args.crawlers:
            if crawler_name in ['yonhap', 'edaily', 'infomax']:
                test_period = {
                    'key': 'test',
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                }
                config = collector.crawlers[crawler_name]
                collector.collect_monthly_news(crawler_name, config, test_period)
    else:
        # 전체 월별 수집
        collector.run_monthly_collection(args.crawlers, args.resume)
    
    # 수집 완료 후 상태 출력
    print("\n" + "="*60)
    collector.print_status()
    
    # 병합 실행 여부 확인
    try:
        if input("\n🔄 수집된 데이터를 병합하시겠습니까? (y/N): ").lower() == 'y':
            merger = DataMerger()
            merger.merge_all_crawlers()
    except (EOFError, KeyboardInterrupt):
        print("\nSkipping merge step...")

if __name__ == "__main__":
    main()
