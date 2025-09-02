#!/usr/bin/env python3
"""
채권 리포트 병렬 수집 스크립트
네이버 금융에서 채권 분석 리포트를 효율적으로 수집
"""

from bs4 import BeautifulSoup
import requests
import time
import re
from requests import get
from urllib import request
from PyPDF2 import PdfReader
import os
import csv
import shutil
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BondReportCrawler:
    def __init__(self, start_date, end_date, output_dir="data/bond_reports", max_workers=5):
        self.start_date = start_date
        self.end_date = end_date
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            'Referer': 'https://www.naver.com/'
        }
        
        # 수집 통계
        self.stats = {
            'total_pages': 0,
            'total_reports': 0,
            'pdf_success': 0,
            'pdf_failed': 0,
            'errors': []
        }
        
    def get_total_pages(self):
        """전체 페이지 수 확인"""
        url = f"https://finance.naver.com/research/debenture_list.naver?keyword=&brokerCode=&searchType=writeDate&writeFromDate={self.start_date}&writeToDate={self.end_date}&x=0&y=0&page=1"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            last_page_elem = soup.select_one('td.pgRR>a')
            if last_page_elem:
                last_page_href = last_page_elem.attrs['href']
                match = re.search(r'page=(\d+)', last_page_href)
                if match:
                    return int(match.group(1))
        except Exception as e:
            logger.error(f"페이지 수 확인 실패: {e}")
        
        return 1
    
    def process_page(self, page_num):
        """개별 페이지 처리"""
        url = f"https://finance.naver.com/research/debenture_list.naver?keyword=&brokerCode=&searchType=writeDate&writeFromDate={self.start_date}&writeToDate={self.end_date}&x=0&y=0&page={page_num}"
        
        results = []
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 리포트 목록 추출
            report_rows = soup.select('table.type_1 tr')
            
            for row in report_rows:
                # 제목이 있는 행만 처리
                title_elem = row.select_one('td.title a')
                if not title_elem:
                    continue
                
                report_data = self.extract_report_info(row, title_elem)
                if report_data:
                    results.append(report_data)
                    
                # 서버 부하 방지
                time.sleep(0.5)
                
        except Exception as e:
            logger.error(f"페이지 {page_num} 처리 실패: {e}")
            self.stats['errors'].append(f"Page {page_num}: {str(e)}")
        
        return results
    
    def extract_report_info(self, row, title_elem):
        """리포트 정보 추출"""
        try:
            # 기본 정보
            title = title_elem.text.strip()
            link = title_elem.get('href', '')
            
            # 증권사
            company = row.select_one('td.file')
            company_name = company.text.strip() if company else ''
            
            # 날짜
            date = row.select_one('td.date')
            report_date = date.text.strip() if date else ''
            
            # 조회수
            view = row.select_one('td.date2')
            view_count = view.text.strip() if view else '0'
            
            # 상세 페이지에서 PDF 링크 추출
            pdf_url = None
            pdf_content = None
            
            if link:
                detail_url = f"https://finance.naver.com/research/{link}"
                try:
                    detail_response = requests.get(detail_url, headers=self.headers, timeout=30)
                    detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                    
                    # PDF 링크 찾기
                    pdf_link_elem = detail_soup.select_one('a.con_link')
                    if pdf_link_elem:
                        pdf_url = pdf_link_elem.get('href', '')
                        
                        # PDF 다운로드 및 텍스트 추출
                        if pdf_url:
                            pdf_content = self.extract_pdf_text(pdf_url, title)
                            
                except Exception as e:
                    logger.warning(f"상세 페이지 처리 실패: {title} - {e}")
            
            return {
                'title': title,
                'company': company_name,
                'date': report_date,
                'view_count': view_count,
                'url': detail_url if link else '',
                'pdf_url': pdf_url,
                'content': pdf_content if pdf_content else '',
                'collected_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"리포트 정보 추출 실패: {e}")
            return None
    
    def extract_pdf_text(self, pdf_url, title):
        """PDF 텍스트 추출"""
        try:
            # PDF 다운로드
            pdf_response = requests.get(pdf_url, timeout=60)
            
            # 임시 파일로 저장
            safe_title = re.sub(r'[^\w\s-]', '_', title)[:50]
            pdf_path = self.output_dir / f"{safe_title}.pdf"
            
            with open(pdf_path, 'wb') as f:
                f.write(pdf_response.content)
            
            # PDF 텍스트 추출
            text = ""
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    try:
                        text += page.extract_text()
                    except:
                        continue
            
            # 텍스트 정제
            text = re.sub(r'\s+', ' ', text)
            text = text[:50000]  # 최대 50,000자로 제한
            
            self.stats['pdf_success'] += 1
            
            return text
            
        except Exception as e:
            logger.warning(f"PDF 처리 실패: {title} - {e}")
            self.stats['pdf_failed'] += 1
            return None
    
    def run_parallel_collection(self):
        """병렬 수집 실행"""
        logger.info(f"수집 시작: {self.start_date} ~ {self.end_date}")
        
        # 전체 페이지 수 확인
        total_pages = self.get_total_pages()
        self.stats['total_pages'] = total_pages
        logger.info(f"전체 페이지 수: {total_pages}")
        
        # 병렬 처리
        all_reports = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 모든 페이지를 작업 큐에 추가
            futures = {
                executor.submit(self.process_page, page): page 
                for page in range(1, total_pages + 1)
            }
            
            # 완료된 작업 처리
            for future in as_completed(futures):
                page = futures[future]
                try:
                    results = future.result()
                    all_reports.extend(results)
                    logger.info(f"페이지 {page}/{total_pages} 완료 - {len(results)}개 리포트")
                except Exception as e:
                    logger.error(f"페이지 {page} 실패: {e}")
        
        self.stats['total_reports'] = len(all_reports)
        
        # 결과 저장
        self.save_results(all_reports)
        
        return all_reports
    
    def save_results(self, reports):
        """결과 저장"""
        # JSON 저장
        json_path = self.output_dir / f"bond_reports_{self.start_date}_{self.end_date}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)
        
        # CSV 저장
        csv_path = self.output_dir / f"bond_reports_{self.start_date}_{self.end_date}.csv"
        if reports:
            keys = reports[0].keys()
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(reports)
        
        # 통계 저장
        stats_path = self.output_dir / f"stats_{self.start_date}_{self.end_date}.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"저장 완료: {json_path}")
        logger.info(f"통계: {self.stats}")


def collect_by_month(year, month):
    """월별 수집 함수"""
    # 월의 첫날과 마지막날 계산
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    
    start_date = datetime(year, month, 1).strftime('%Y-%m-%d')
    end_date = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
    
    logger.info(f"\n{'='*50}")
    logger.info(f"{year}년 {month}월 수집 시작")
    logger.info(f"기간: {start_date} ~ {end_date}")
    logger.info(f"{'='*50}")
    
    crawler = BondReportCrawler(start_date, end_date, max_workers=5)
    reports = crawler.run_parallel_collection()
    
    return len(reports)


def main():
    """메인 실행 함수"""
    import sys
    
    # 명령행 인자 처리
    if len(sys.argv) >= 3:
        start_date = sys.argv[1]
        end_date = sys.argv[2]
        max_workers = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    else:
        # 기본값: 최근 1개월
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        max_workers = 5
    
    logger.info(f"채권 리포트 수집 시작")
    logger.info(f"기간: {start_date} ~ {end_date}")
    logger.info(f"병렬 작업자: {max_workers}개")
    
    crawler = BondReportCrawler(start_date, end_date, max_workers=max_workers)
    reports = crawler.run_parallel_collection()
    
    logger.info(f"수집 완료: 총 {len(reports)}개 리포트")


if __name__ == "__main__":
    main()