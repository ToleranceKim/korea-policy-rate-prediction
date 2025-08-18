#!/usr/bin/env python3
"""
MPB 통화정책 스탠스 분석을 위한 데이터 수집 스크립트
수집 기간: 2014.08 ~ 2025.08 (약 11년치)
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class StanceMiningCrawler:
    def __init__(self):
        self.start_date = "2014-08-11"  # 현재 프로젝트 시작일
        self.end_date = "2025-08-11"    # 확장 종료일  
        self.mpb_start = "2014-08-11"   # MPB 회의록
        self.news_start = "2014-08-11"  # 뉴스/채권
        
        # 예상 수집 건수 (11년치)
        self.estimated_counts = {
            'mpb': 100,      # 약 100차례 회의록 (연 8-9회)
            'news': 350000,  # 약 35만건 뉴스 (연 3만건)
            'bond': 35000    # 약 3.5만건 채권 보고서 (연 3천건)
        }
        
        print(f"📋 MPB 스탠스 분석용 데이터 수집 시작")
        print(f"📅 수집 기간: {self.start_date} ~ {self.end_date} (약 11년)")
        print(f"🎯 예상: MPB {self.estimated_counts['mpb']}건, 뉴스 {self.estimated_counts['news']:,}건, 채권 {self.estimated_counts['bond']:,}건")
        print(f"💾 스토리지 절약을 위해 최근 11년 데이터만 수집")

    def run_mpb_crawler(self):
        """MPB 회의록 크롤링 (2005.05~2017.12)"""
        print("\n🏛️ MPB 회의록 크롤링 시작...")
        
        # MPB 크롤러 실행 (Scrapy)
        os.chdir('crawler/MPB')
        try:
            result = subprocess.run([
                'scrapy', 'crawl', 'mpb_crawler', 
                '-s', 'FEEDS={"../../data/raw/mpb_minutes.json": {"format": "json"}}'
            ], capture_output=True, text=True, timeout=7200)  # 2시간 타임아웃
            
            if result.returncode == 0:
                print("✅ MPB 크롤링 완료")
            else:
                print(f"❌ MPB 크롤링 실패: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("⏰ MPB 크롤링 타임아웃 (2시간 초과)")
        finally:
            os.chdir('../..')

    def run_news_crawlers(self):
        """뉴스 크롤링 (연합인포맥스, 이데일리, 연합뉴스)"""
        print("\n📰 뉴스 크롤링 시작...")
        
        # 연합뉴스 크롤링 (API 기반)
        self._run_yonhap_crawler()
        
        # 이데일리 크롤링 (6개월 분할)
        self._run_edaily_crawler()
        
        # 인포맥스는 현재 1일치만 구현되어 있어 스킵
        print("⚠️ 인포맥스 크롤러는 별도 구현 필요")

    def _run_yonhap_crawler(self):
        """연합뉴스 크롤링"""
        print("📻 연합뉴스 크롤링...")
        
        # 날짜 범위 생성 (월별 분할)
        start = datetime.strptime(self.news_start, '%Y-%m-%d')
        end = datetime.strptime(self.end_date, '%Y-%m-%d')
        
        current = start
        while current <= end:
            month_end = min(current + relativedelta(months=1) - timedelta(days=1), end)
            print(f"  📅 수집 중: {current.strftime('%Y-%m-%d')} ~ {month_end.strftime('%Y-%m-%d')}")
            current = month_end + timedelta(days=1)
        
        print("ℹ️ 연합뉴스: 스크립트 수정 후 실행 가능")

    def _run_edaily_crawler(self):
        """이데일리 크롤링 (6개월 단위)"""
        print("📺 이데일리 크롤링...")
        
        # 6개월 단위로 분할
        start = datetime.strptime(self.news_start, '%Y-%m-%d')
        end = datetime.strptime(self.end_date, '%Y-%m-%d')
        
        periods = []
        current = start
        while current <= end:
            period_end = min(current + relativedelta(months=6) - timedelta(days=1), end)
            periods.append((current, period_end))
            current = period_end + timedelta(days=1)
        
        print(f"  📊 총 {len(periods)}개 기간으로 분할")
        for i, (p_start, p_end) in enumerate(periods, 1):
            print(f"  📅 기간 {i}: {p_start.strftime('%Y-%m-%d')} ~ {p_end.strftime('%Y-%m-%d')}")
        
        print("ℹ️ 이데일리: 6개월 분할 로직 구현 후 실행")

    def run_bond_crawler(self):
        """채권 보고서 크롤링 (2005.01~2017.12)"""
        print("\n💰 채권 보고서 크롤링 시작...")
        
        # 채권 크롤러는 기간이 너무 길면 타임아웃 위험
        # 1년 단위로 분할 실행 권장
        start_year = 2005
        end_year = 2017
        
        for year in range(start_year, end_year + 1):
            print(f"  📅 {year}년 채권 보고서 수집...")
            # 실제 실행은 bond_crawling.py 수정 후
        
        print("ℹ️ 채권: 날짜 범위 수정 후 실행 가능")

    def validate_data(self):
        """수집된 데이터 검증"""
        print("\n🔍 데이터 수집 결과 검증...")
        
        # 파일 존재 확인
        data_files = [
            'data/raw/mpb_minutes.json',
            'data/raw/yonhap_news.csv',
            'data/raw/edaily_news.csv',
            'data/raw/bond_reports.csv'
        ]
        
        for file_path in data_files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path) / (1024*1024)  # MB
                print(f"  ✅ {file_path}: {size:.1f}MB")
            else:
                print(f"  ❌ {file_path}: 파일 없음")
        
        print("\n📊 예상 수집률:")
        print(f"  🏛️ MPB: ? / {self.estimated_counts['mpb']} (예상)")
        print(f"  📰 뉴스: ? / {self.estimated_counts['news']:,} (예상)")
        print(f"  💰 채권: ? / {self.estimated_counts['bond']:,} (예상)")

    def run(self):
        """전체 크롤링 프로세스 실행"""
        print("🚀 MPB 스탠스 분석용 데이터 수집 시작\n")
        
        # 데이터 디렉토리 생성
        os.makedirs('data/raw', exist_ok=True)
        
        try:
            # 1단계: MPB 회의록 (가장 중요)
            self.run_mpb_crawler()
            
            # 2단계: 뉴스 기사
            self.run_news_crawlers()
            
            # 3단계: 채권 보고서
            self.run_bond_crawler()
            
            # 4단계: 데이터 검증
            self.validate_data()
            
            print("\n🎉 데이터 수집 프로세스 완료!")
            print("⚠️ 일부 크롤러는 날짜 수정 후 개별 실행 필요")
            
        except KeyboardInterrupt:
            print("\n⛔ 사용자에 의해 중단됨")
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")

if __name__ == "__main__":
    crawler = StanceMiningCrawler()
    crawler.run() 