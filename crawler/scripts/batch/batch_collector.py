#!/usr/bin/env python3
"""
월별 분할 수집 시스템
- 10년간의 데이터를 월별로 안전하게 수집
- 실패 시 재시작 기능
- 진행상황 추적 및 데이터 중복 방지
"""

import os
import json
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging

class BatchCollector:
    def __init__(self, base_dir="/Users/lord_jubin/Desktop/my_git/mpb-stance-mining/crawler"):
        self.base_dir = Path(base_dir)
        self.progress_file = self.base_dir / "batch_progress.json"
        self.output_dir = self.base_dir / "data" / "monthly"
        self.output_dir.mkdir(exist_ok=True)
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.base_dir / "logs" / "batch_collector.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 수집 대상 크롤러 설정
        self.crawlers = {
            'yonhap': {
                'path': 'yh/yh_crawler',
                'spider': 'yh_fixed',
                'supports_monthly': True
            },
            'edaily': {
                'path': 'edaily/edaily_crawler', 
                'spider': 'edaily_fixed',
                'supports_monthly': True
            },
            'infomax': {
                'path': 'InfoMax/infomax_crawler',
                'spider': 'infomax_fixed', 
                'supports_monthly': True
            },
            'bond': {
                'path': 'BOND',
                'script': 'bond_crawling.py',
                'supports_monthly': True
            },
            'interest_rates': {
                'path': 'interest_rates/interest_rates_crawler',
                'spider': 'interest_rates',
                'supports_monthly': False  # 전체 수집만 가능
            },
            'call_ratings': {
                'path': 'call_ratings/call_ratings_crawler', 
                'spider': 'call_ratings',
                'supports_monthly': False  # 전체 수집만 가능
            },
            'mpb': {
                'path': 'MPB/mpb_crawler',
                'spider': 'mpb_crawler', 
                'supports_monthly': False  # 전체 수집만 가능
            }
        }
        
        # 진행상황 로드
        self.progress = self.load_progress()
    
    def load_progress(self):
        """진행상황 로드"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'completed_months': {},
            'failed_months': {},
            'last_run': None,
            'total_collected': 0
        }
    
    def save_progress(self):
        """진행상황 저장"""
        self.progress['last_run'] = datetime.now().isoformat()
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, indent=2, ensure_ascii=False)
    
    def generate_monthly_periods(self, start_year=2015, end_year=2025, end_month=8):
        """월별 수집 기간 생성"""
        periods = []
        for year in range(start_year, end_year + 1):
            start_month = 1
            last_month = 12 if year < end_year else end_month
            
            for month in range(start_month, last_month + 1):
                # 월 시작일과 종료일 계산
                start_date = datetime(year, month, 1)
                if month == 12:
                    end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = datetime(year, month + 1, 1) - timedelta(days=1)
                
                period_key = f"{year:04d}-{month:02d}"
                periods.append({
                    'key': period_key,
                    'year': year,
                    'month': month,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                })
        
        return periods
    
    def is_month_completed(self, crawler_name, period_key):
        """특정 월의 수집이 완료되었는지 확인"""
        return (crawler_name in self.progress['completed_months'] and 
                period_key in self.progress['completed_months'][crawler_name])
    
    def mark_month_completed(self, crawler_name, period_key, output_file, item_count):
        """월별 수집 완료 표시"""
        if crawler_name not in self.progress['completed_months']:
            self.progress['completed_months'][crawler_name] = {}
        
        self.progress['completed_months'][crawler_name][period_key] = {
            'completed_at': datetime.now().isoformat(),
            'output_file': str(output_file),
            'item_count': item_count
        }
        
        self.progress['total_collected'] += item_count
        self.save_progress()
    
    def mark_month_failed(self, crawler_name, period_key, error_msg):
        """월별 수집 실패 표시"""
        if crawler_name not in self.progress['failed_months']:
            self.progress['failed_months'][crawler_name] = {}
        
        self.progress['failed_months'][crawler_name][period_key] = {
            'failed_at': datetime.now().isoformat(),
            'error': error_msg
        }
        
        self.save_progress()
    
    def collect_monthly_news(self, crawler_name, config, period):
        """뉴스 크롤러 월별 수집"""
        period_key = period['key']
        output_file = self.output_dir / f"{crawler_name}_{period_key}.json"
        
        # 이미 수집된 경우 건너뛰기
        if self.is_month_completed(crawler_name, period_key):
            self.logger.info(f"⏭️ {crawler_name} {period_key} already completed, skipping...")
            return True
        
        self.logger.info(f"🚀 Starting {crawler_name} collection for {period_key}")
        
        try:
            crawler_dir = self.base_dir / config['path']
            cmd = [
                '/opt/anaconda3/envs/ds_env/bin/scrapy', 'crawl', config['spider'],
                '-o', str(output_file),
                '-s', 'CLOSESPIDER_PAGECOUNT=10',  # 테스트용 제한
                '-a', f'start_date={period["start_date"]}',
                '-a', f'end_date={period["end_date"]}'
            ]
            
            result = subprocess.run(
                cmd, 
                cwd=crawler_dir,
                capture_output=True, 
                text=True,
                timeout=1800  # 30분 타임아웃
            )
            
            if result.returncode == 0:
                # 수집된 아이템 수 확인
                item_count = self.count_json_items(output_file)
                self.mark_month_completed(crawler_name, period_key, output_file, item_count)
                self.logger.info(f"✅ {crawler_name} {period_key} completed: {item_count} items")
                return True
            else:
                error_msg = f"Scrapy failed: {result.stderr}"
                self.mark_month_failed(crawler_name, period_key, error_msg)
                self.logger.error(f"❌ {crawler_name} {period_key} failed: {error_msg}")
                return False
                
        except subprocess.TimeoutExpired:
            error_msg = "Collection timeout (30 minutes)"
            self.mark_month_failed(crawler_name, period_key, error_msg)
            self.logger.error(f"⏰ {crawler_name} {period_key} timed out")
            return False
        except Exception as e:
            error_msg = str(e)
            self.mark_month_failed(crawler_name, period_key, error_msg)
            self.logger.error(f"💥 {crawler_name} {period_key} error: {error_msg}")
            return False
    
    def collect_full_dataset(self, crawler_name, config):
        """전체 데이터 수집 (월별 분할 불가능한 크롤러용)"""
        output_file = self.output_dir / f"{crawler_name}_full.json"
        
        # 이미 수집된 경우 건너뛰기
        if self.is_month_completed(crawler_name, 'full'):
            self.logger.info(f"⏭️ {crawler_name} full dataset already completed, skipping...")
            return True
        
        self.logger.info(f"🚀 Starting {crawler_name} full collection")
        
        try:
            crawler_dir = self.base_dir / config['path']
            
            if 'spider' in config:
                # Scrapy 크롤러
                cmd = [
                    '/opt/anaconda3/envs/ds_env/bin/scrapy', 'crawl', config['spider'],
                    '-o', str(output_file)
                ]
                result = subprocess.run(cmd, cwd=crawler_dir, capture_output=True, text=True, timeout=3600)
            else:
                # Python 스크립트
                cmd = ['/opt/anaconda3/envs/ds_env/bin/python', config['script']]
                result = subprocess.run(cmd, cwd=crawler_dir, capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                item_count = self.count_json_items(output_file) if output_file.exists() else 0
                self.mark_month_completed(crawler_name, 'full', output_file, item_count)
                self.logger.info(f"✅ {crawler_name} full dataset completed: {item_count} items")
                return True
            else:
                error_msg = f"Collection failed: {result.stderr}"
                self.mark_month_failed(crawler_name, 'full', error_msg)
                self.logger.error(f"❌ {crawler_name} full dataset failed: {error_msg}")
                return False
                
        except Exception as e:
            error_msg = str(e)
            self.mark_month_failed(crawler_name, 'full', error_msg)
            self.logger.error(f"💥 {crawler_name} full dataset error: {error_msg}")
            return False
    
    def count_json_items(self, file_path):
        """JSON 파일의 아이템 수 세기"""
        try:
            if not file_path.exists():
                return 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return len(data) if isinstance(data, list) else 1
        except:
            return 0
    
    def run_monthly_collection(self, crawler_names=None, resume_from=None):
        """월별 분할 수집 실행"""
        if crawler_names is None:
            crawler_names = list(self.crawlers.keys())
        
        periods = self.generate_monthly_periods()
        
        # 재시작 지점 찾기
        start_idx = 0
        if resume_from:
            for i, period in enumerate(periods):
                if period['key'] == resume_from:
                    start_idx = i
                    break
        
        self.logger.info(f"📅 Starting monthly collection for {len(periods)} periods")
        self.logger.info(f"🎯 Target crawlers: {crawler_names}")
        
        for crawler_name in crawler_names:
            if crawler_name not in self.crawlers:
                self.logger.warning(f"Unknown crawler: {crawler_name}")
                continue
                
            config = self.crawlers[crawler_name]
            
            if not config['supports_monthly']:
                # 전체 수집만 가능한 크롤러
                self.collect_full_dataset(crawler_name, config)
                continue
            
            # 월별 수집 가능한 크롤러
            success_count = 0
            total_periods = len(periods[start_idx:])
            
            for period in periods[start_idx:]:
                success = self.collect_monthly_news(crawler_name, config, period)
                if success:
                    success_count += 1
                
                # 수집 간 대기 (서버 부하 방지)
                time.sleep(5)
                
                # 진행률 출력
                progress_pct = (success_count / total_periods) * 100
                self.logger.info(f"📊 {crawler_name} progress: {success_count}/{total_periods} ({progress_pct:.1f}%)")
            
            self.logger.info(f"🎉 {crawler_name} monthly collection completed: {success_count}/{total_periods} successful")
    
    def print_status(self):
        """현재 수집 상태 출력"""
        print("\n" + "="*60)
        print("📊 BATCH COLLECTION STATUS")
        print("="*60)
        
        print(f"📈 Total items collected: {self.progress['total_collected']:,}")
        print(f"🕐 Last run: {self.progress.get('last_run', 'Never')}")
        
        print("\n🎯 CRAWLER STATUS:")
        for crawler_name in self.crawlers:
            completed = len(self.progress['completed_months'].get(crawler_name, {}))
            failed = len(self.progress['failed_months'].get(crawler_name, {}))
            print(f"  {crawler_name:15} ✅ {completed:3d} completed  ❌ {failed:2d} failed")
        
        if self.progress['failed_months']:
            print("\n❌ FAILED COLLECTIONS:")
            for crawler_name, failures in self.progress['failed_months'].items():
                for period, info in failures.items():
                    print(f"  {crawler_name} {period}: {info['error'][:50]}...")


if __name__ == "__main__":
    collector = BatchCollector()
    
    # 현재 상태 출력
    collector.print_status()
    
    # 수집 시작 (테스트용으로 뉴스 크롤러만)
    print("\n🚀 Starting test collection...")
    collector.run_monthly_collection(['yonhap', 'edaily', 'infomax'])