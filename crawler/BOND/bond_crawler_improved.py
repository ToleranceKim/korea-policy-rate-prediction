#!/usr/bin/env python3
"""
개선된 채권 리포트 크롤러
- 재시도 로직
- 에러 핸들링 강화
- 진행상황 추적
- 0바이트 파일 방지
"""

import os
import sys
import time
import json
import csv
import logging
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
import hashlib

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bond_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BondCrawler:
    def __init__(self, start_date=None, end_date=None):
        """
        초기화
        Args:
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
        """
        self.start_date = start_date or "2014-01-01"
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        
        self.base_url = "https://finance.naver.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # 세션 사용으로 연결 재사용
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 통계
        self.stats = {
            'total_pages': 0,
            'total_reports': 0,
            'successful_pdfs': 0,
            'failed_pdfs': 0,
            'skipped_no_pdf': 0,
            'retry_count': 0
        }
        
        # 데이터 저장 디렉토리
        self.pdf_dir = "./pdfs"
        self.csv_dir = "./dataset_improved"
        os.makedirs(self.pdf_dir, exist_ok=True)
        os.makedirs(self.csv_dir, exist_ok=True)
        
        # 이미 처리된 파일 추적
        self.processed_file = "processed_reports.json"
        self.processed = self.load_processed()
    
    def load_processed(self):
        """이미 처리된 리포트 로드"""
        if os.path.exists(self.processed_file):
            with open(self.processed_file, 'r') as f:
                return set(json.load(f))
        return set()
    
    def save_processed(self):
        """처리된 리포트 저장"""
        with open(self.processed_file, 'w') as f:
            json.dump(list(self.processed), f, indent=2)
    
    def get_total_pages(self):
        """전체 페이지 수 확인"""
        url = f"{self.base_url}/research/debenture_list.naver"
        params = {
            'keyword': '',
            'brokerCode': '',
            'searchType': 'writeDate',
            'writeFromDate': self.start_date,
            'writeToDate': self.end_date,
            'page': 1
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 마지막 페이지 번호 찾기
            last_page_link = soup.select_one('td.pgRR > a')
            if last_page_link:
                href = last_page_link.get('href', '')
                import re
                match = re.search(r'page=(\d+)', href)
                if match:
                    return int(match.group(1))
            
            # 페이지 링크에서 최대값 찾기
            page_links = soup.select('table.Nnavi a')
            pages = []
            for link in page_links:
                try:
                    page_num = int(link.text.strip())
                    pages.append(page_num)
                except:
                    pass
            
            return max(pages) if pages else 1
            
        except Exception as e:
            logger.error(f"전체 페이지 수 확인 실패: {e}")
            return 100  # 기본값
    
    def download_with_retry(self, url, max_retries=3, timeout=30):
        """재시도 로직이 포함된 다운로드"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=timeout, stream=True)
                
                # 상태 코드 확인
                if response.status_code == 200:
                    content = response.content
                    # 0바이트 확인
                    if len(content) > 0:
                        return content
                    else:
                        logger.warning(f"0바이트 응답: {url}")
                elif response.status_code == 404:
                    logger.warning(f"404 Not Found: {url}")
                    return None
                else:
                    logger.warning(f"HTTP {response.status_code}: {url}")
                
            except requests.exceptions.Timeout:
                logger.warning(f"타임아웃 (시도 {attempt+1}/{max_retries}): {url}")
            except requests.exceptions.ConnectionError:
                logger.warning(f"연결 오류 (시도 {attempt+1}/{max_retries}): {url}")
            except Exception as e:
                logger.error(f"다운로드 오류: {e}")
            
            # 재시도 전 대기
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 지수 백오프
                time.sleep(wait_time)
                self.stats['retry_count'] += 1
        
        return None
    
    def process_report(self, report_url, title, company, date):
        """개별 리포트 처리"""
        # 중복 확인
        report_id = hashlib.md5(f"{title}_{company}_{date}".encode()).hexdigest()
        if report_id in self.processed:
            logger.debug(f"이미 처리됨: {title}")
            return
        
        try:
            # 리포트 페이지 접근
            response = self.session.get(report_url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # PDF 링크 찾기
            pdf_link = None
            for link in soup.select('a.con_link'):
                href = link.get('href', '')
                if '.pdf' in href.lower():
                    pdf_link = href
                    break
            
            if not pdf_link:
                logger.info(f"PDF 없음: {title}")
                self.stats['skipped_no_pdf'] += 1
                return
            
            # PDF 다운로드
            pdf_content = self.download_with_retry(pdf_link)
            if not pdf_content:
                logger.error(f"PDF 다운로드 실패: {title}")
                self.stats['failed_pdfs'] += 1
                return
            
            # PDF 저장
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            pdf_filename = f"{date}_{safe_title}_{company}.pdf"
            pdf_path = os.path.join(self.pdf_dir, pdf_filename)
            
            with open(pdf_path, 'wb') as f:
                f.write(pdf_content)
            
            # PDF 텍스트 추출
            text_content = self.extract_pdf_text(pdf_path)
            
            # CSV 저장
            csv_filename = f"{date}_{safe_title}_{company}.csv"
            csv_path = os.path.join(self.csv_dir, csv_filename)
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Date', 'Title', 'Company', 'Content', 'PDF_URL'])
                writer.writerow([date, title, company, text_content, pdf_link])
            
            # 성공 기록
            self.processed.add(report_id)
            self.stats['successful_pdfs'] += 1
            logger.info(f"✓ 수집 완료: {title}")
            
            # 메모리 관리 - PDF 파일 삭제 옵션
            if os.path.getsize(pdf_path) > 10 * 1024 * 1024:  # 10MB 이상
                os.remove(pdf_path)
                logger.debug(f"대용량 PDF 삭제: {pdf_filename}")
            
        except Exception as e:
            logger.error(f"리포트 처리 실패 ({title}): {e}")
            self.stats['failed_pdfs'] += 1
    
    def extract_pdf_text(self, pdf_path):
        """PDF 텍스트 추출"""
        try:
            with open(pdf_path, 'rb') as f:
                pdf_reader = PdfReader(f)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                # 텍스트 정제
                text = ' '.join(text.split())
                return text[:50000]  # 최대 50000자
        except Exception as e:
            logger.error(f"PDF 텍스트 추출 실패: {e}")
            return ""
    
    def process_page(self, page_num):
        """페이지별 리포트 목록 처리"""
        url = f"{self.base_url}/research/debenture_list.naver"
        params = {
            'keyword': '',
            'brokerCode': '',
            'searchType': 'writeDate', 
            'writeFromDate': self.start_date,
            'writeToDate': self.end_date,
            'page': page_num
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            reports = []
            for row in soup.select('table.type_1 tr'):
                link = row.select_one('a')
                if not link:
                    continue
                
                # 정보 추출
                title = link.text.strip()
                href = link.get('href', '')
                report_url = urljoin(self.base_url + '/research/', href)
                
                # 회사명과 날짜 추출
                info_cells = row.select('td')
                if len(info_cells) >= 3:
                    company = info_cells[2].text.strip()
                    date = info_cells[1].text.strip()
                    
                    reports.append({
                        'url': report_url,
                        'title': title,
                        'company': company,
                        'date': date
                    })
            
            logger.info(f"페이지 {page_num}: {len(reports)}개 리포트 발견")
            return reports
            
        except Exception as e:
            logger.error(f"페이지 {page_num} 처리 실패: {e}")
            return []
    
    def run(self, max_workers=5):
        """크롤링 실행"""
        logger.info("="*60)
        logger.info(f"채권 리포트 크롤링 시작")
        logger.info(f"기간: {self.start_date} ~ {self.end_date}")
        logger.info("="*60)
        
        # 전체 페이지 수 확인
        total_pages = self.get_total_pages()
        self.stats['total_pages'] = total_pages
        logger.info(f"전체 페이지 수: {total_pages}")
        
        # 페이지별 리포트 수집
        all_reports = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.process_page, page) for page in range(1, total_pages + 1)]
            
            for future in as_completed(futures):
                reports = future.result()
                all_reports.extend(reports)
        
        self.stats['total_reports'] = len(all_reports)
        logger.info(f"전체 리포트 수: {len(all_reports)}")
        
        # 리포트별 PDF 다운로드 및 처리
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for report in all_reports:
                future = executor.submit(
                    self.process_report,
                    report['url'],
                    report['title'],
                    report['company'],
                    report['date']
                )
                futures.append(future)
            
            # 진행상황 표시
            completed = 0
            for future in as_completed(futures):
                completed += 1
                if completed % 100 == 0:
                    logger.info(f"진행: {completed}/{len(all_reports)}")
                    self.save_processed()  # 중간 저장
        
        # 최종 저장
        self.save_processed()
        
        # 통계 출력
        logger.info("="*60)
        logger.info("크롤링 완료 통계")
        logger.info(f"전체 페이지: {self.stats['total_pages']}")
        logger.info(f"전체 리포트: {self.stats['total_reports']}")
        logger.info(f"성공 PDF: {self.stats['successful_pdfs']}")
        logger.info(f"실패 PDF: {self.stats['failed_pdfs']}")
        logger.info(f"PDF 없음: {self.stats['skipped_no_pdf']}")
        logger.info(f"재시도 횟수: {self.stats['retry_count']}")
        success_rate = (self.stats['successful_pdfs'] / self.stats['total_reports'] * 100) if self.stats['total_reports'] > 0 else 0
        logger.info(f"성공률: {success_rate:.1f}%")
        logger.info("="*60)

if __name__ == "__main__":
    # 명령행 인자 처리
    if len(sys.argv) >= 3:
        start_date = sys.argv[1]
        end_date = sys.argv[2]
    else:
        start_date = "2014-01-01"
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # 크롤러 실행
    crawler = BondCrawler(start_date, end_date)
    crawler.run(max_workers=5)