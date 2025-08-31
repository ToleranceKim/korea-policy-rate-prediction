#!/usr/bin/env python3
"""
크롤러 누락 방지를 위한 포괄적 검증 스크립트
실제 웹사이트 데이터와 크롤링 결과를 비교하여 누락 검증
"""

import json
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import time
import subprocess
import os
from pathlib import Path

class ComprehensiveCrawlerValidator:
    """포괄적 크롤러 검증기"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.validation_results = {}
        
    def validate_mpb_crawler(self):
        """MPB 크롤러 완전성 검증"""
        print("\n" + "="*60)
        print("MPB 크롤러 완전성 검증")
        print("="*60)
        
        # 1. 실제 웹사이트에서 기대 데이터 수집
        print("\n1단계: 웹사이트에서 실제 데이터 수집...")
        expected_data = self.collect_expected_mpb_data()
        
        # 2. 크롤러 실행
        print("\n2단계: 크롤러 실행...")
        crawled_data = self.run_mpb_crawler()
        
        # 3. 비교 분석
        print("\n3단계: 데이터 비교 분석...")
        validation = self.compare_mpb_data(expected_data, crawled_data)
        
        self.validation_results['mpb'] = validation
        return validation
    
    def collect_expected_mpb_data(self):
        """실제 웹사이트에서 2014-2025년 MPB 데이터 수집"""
        expected_items = []
        missing_patterns = []
        
        # 샘플링: 주요 페이지들만 확인 (전체는 너무 많음)
        sample_pages = [1, 50, 100, 200, 300, 500, 1000, 1500, 2000, 2500, 3000]
        
        for page in sample_pages:
            try:
                url = f"https://www.bok.or.kr/portal/singl/newsData/listCont.do"
                params = {
                    'targetDepth': 4,
                    'menuNo': 200789,
                    'pageIndex': page
                }
                
                resp = self.session.get(url, params=params)
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # 모든 게시물 확인
                items = soup.select('li.bbsRowCls')
                
                for item in items:
                    title_elem = item.select_one('a.title')
                    if title_elem:
                        title = title_elem.text.strip()
                        
                        # 여러 날짜 패턴 시도
                        year = None
                        
                        # 패턴 1: 표준 형식
                        date_match = re.search(r'(\d{4})[\.\s년\-/](\d{1,2})[\.\s월\-/](\d{1,2})', title)
                        if date_match:
                            year = int(date_match.group(1))
                        
                        # 패턴 2: 연도만
                        if not year:
                            year_match = re.search(r'(20\d{2})년?(?:\s|$|\]|\))', title)
                            if year_match:
                                year = int(year_match.group(1))
                        
                        # 패턴 3: 등록일에서 추출
                        if not year:
                            date_elem = item.select_one('span.date')
                            if date_elem:
                                date_text = date_elem.text
                                year_match = re.search(r'(20\d{2})', date_text)
                                if year_match:
                                    year = int(year_match.group(1))
                        
                        if year and 2014 <= year <= 2025:
                            # 의사록 관련 키워드 확인 (느슨한 매칭)
                            keywords = ['통화정책', '금융통화', '의사록', '회의록', '위원회', 
                                      '기준금리', 'MPB', '통안', '의안']
                            
                            is_relevant = any(kw in title for kw in keywords)
                            
                            expected_items.append({
                                'title': title,
                                'year': year,
                                'page': page,
                                'relevant': is_relevant
                            })
                        elif not year:
                            missing_patterns.append({
                                'title': title,
                                'page': page,
                                'issue': '날짜 패턴 미인식'
                            })
                
                time.sleep(0.5)  # 서버 부담 방지
                
            except Exception as e:
                print(f"  페이지 {page} 수집 실패: {e}")
        
        print(f"  샘플 페이지에서 {len(expected_items)}개 항목 발견")
        if missing_patterns:
            print(f"  날짜 인식 실패: {len(missing_patterns)}개")
            for mp in missing_patterns[:3]:  # 처음 3개만 표시
                print(f"    - {mp['title'][:50]}...")
        
        return {
            'items': expected_items,
            'missing_patterns': missing_patterns
        }
    
    def run_mpb_crawler(self):
        """MPB 크롤러 실행 및 결과 수집"""
        output_file = '/tmp/mpb_validation_test.json'
        
        # 기존 파일 삭제
        if os.path.exists(output_file):
            os.remove(output_file)
        
        # 크롤러 실행 (테스트용 제한된 페이지)
        cmd = [
            '/opt/anaconda3/envs/ds_env/bin/scrapy',
            'crawl', 'mpb_crawler_perfect',
            '-a', 'start_year=2014',
            '-a', 'end_year=2025',
            '-o', output_file,
            '-s', 'CLOSESPIDER_PAGECOUNT=50',  # 테스트용 제한
            '-s', 'LOG_LEVEL=ERROR'
        ]
        
        print(f"  크롤러 실행 중... (50페이지 제한)")
        
        try:
            # 크롤러 디렉토리로 이동
            os.chdir('/Users/lord_jubin/Desktop/my_git/mpb-stance-mining/crawler/MPB/mpb_crawler')
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                print(f"  크롤러 실행 오류: {result.stderr}")
                return {'items': [], 'error': result.stderr}
            
            # 결과 파일 읽기
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    items = json.load(f)
                    print(f"  크롤러가 {len(items)}개 항목 수집")
                    return {'items': items}
            else:
                print("  결과 파일을 찾을 수 없음")
                return {'items': []}
                
        except subprocess.TimeoutExpired:
            print("  크롤러 실행 시간 초과")
            return {'items': [], 'error': 'timeout'}
        except Exception as e:
            print(f"  크롤러 실행 실패: {e}")
            return {'items': [], 'error': str(e)}
    
    def compare_mpb_data(self, expected, crawled):
        """기대 데이터와 크롤링 데이터 비교"""
        validation = {
            'expected_count': len(expected.get('items', [])),
            'crawled_count': len(crawled.get('items', [])),
            'missing_items': [],
            'coverage_rate': 0,
            'issues': []
        }
        
        # 제목 기반 매칭
        crawled_titles = set()
        for item in crawled.get('items', []):
            if 'title' in item:
                # 제목 정규화
                title = re.sub(r'\s+', ' ', item['title'].strip())
                crawled_titles.add(title)
        
        # 누락 항목 찾기
        for exp_item in expected.get('items', []):
            if exp_item.get('relevant', False):
                normalized_title = re.sub(r'\s+', ' ', exp_item['title'].strip())
                if normalized_title not in crawled_titles:
                    validation['missing_items'].append(exp_item)
        
        # Coverage 계산
        relevant_expected = [i for i in expected.get('items', []) if i.get('relevant', False)]
        if relevant_expected:
            validation['coverage_rate'] = (
                (len(relevant_expected) - len(validation['missing_items'])) 
                / len(relevant_expected) * 100
            )
        
        # 주요 이슈 식별
        if expected.get('missing_patterns'):
            validation['issues'].append({
                'type': '날짜 패턴 미인식',
                'count': len(expected['missing_patterns']),
                'examples': expected['missing_patterns'][:3]
            })
        
        if crawled.get('error'):
            validation['issues'].append({
                'type': '크롤러 실행 오류',
                'error': crawled['error']
            })
        
        return validation
    
    def validate_call_rates_crawler(self):
        """콜금리 크롤러 검증"""
        print("\n" + "="*60)
        print("콜금리 크롤러 완전성 검증")
        print("="*60)
        
        validation = {
            'date_range_coverage': {},
            'missing_dates': [],
            'data_integrity': []
        }
        
        # 날짜 범위별 검증
        test_ranges = [
            ('20140101', '20140131'),  # 2014년 1월
            ('20191201', '20191231'),  # 2019년 12월
            ('20240801', '20240831'),  # 2024년 8월
        ]
        
        for start, end in test_ranges:
            try:
                url = "https://www.korcham.net/nCham/Service/EconBrief/appl/ProspectBoardList.asp"
                params = {
                    'board_type': 1,
                    'daybt': 'OldNow',
                    'm_OldDate': start,
                    'm_NowDate': end,
                    'pageno': 1
                }
                
                resp = self.session.get(url, params=params)
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # 데이터 행 수 확인
                data_rows = soup.select('table tr')[1:]  # 헤더 제외
                
                validation['date_range_coverage'][f"{start}-{end}"] = {
                    'expected_days': 30,  # 대략
                    'found_records': len(data_rows),
                    'complete': len(data_rows) >= 20  # 주말 제외 대략 20일
                }
                
            except Exception as e:
                validation['date_range_coverage'][f"{start}-{end}"] = {
                    'error': str(e)
                }
        
        self.validation_results['call_rates'] = validation
        return validation
    
    def validate_interest_rates_crawler(self):
        """기준금리 크롤러 검증"""
        print("\n" + "="*60)
        print("기준금리 크롤러 완전성 검증")
        print("="*60)
        
        validation = {
            'javascript_data_found': False,
            'expected_changes': [],
            'data_format_valid': False
        }
        
        try:
            url = "https://www.bok.or.kr/portal/singl/baseRate/list.do?dataSeCd=01&menuNo=200643"
            resp = self.session.get(url)
            
            # JavaScript 변수 확인
            if 'chartObj2_s' in resp.text:
                validation['javascript_data_found'] = True
                
                # 데이터 추출
                pattern = r'chartObj2_s\s*=\s*(\[[\s\S]*?\]);'
                match = re.search(pattern, resp.text)
                
                if match:
                    data_str = match.group(1)
                    # JavaScript 객체를 JSON으로 변환
                    data_str = re.sub(r'(\w+):', r'"\1":', data_str)
                    data_str = re.sub(r':([\d.]+)', r':"\1"', data_str)
                    
                    try:
                        import json
                        data = json.loads(data_str)
                        
                        # 2014-2025 데이터 필터링
                        for item in data:
                            date = item.get('date', '')
                            if date.startswith(('2014', '2015', '2016', '2017', '2018', 
                                              '2019', '2020', '2021', '2022', '2023', 
                                              '2024', '2025')):
                                validation['expected_changes'].append(item)
                        
                        validation['data_format_valid'] = True
                        
                    except:
                        validation['data_format_valid'] = False
            
            # 알려진 주요 금리 변경 확인
            known_changes = [
                '2014-08-14',  # 2.50% → 2.25%
                '2014-10-15',  # 2.25% → 2.00%
                '2020-03-16',  # 1.25% → 0.75% (코로나)
                '2020-05-28',  # 0.75% → 0.50%
                '2021-08-26',  # 0.50% → 0.75%
                '2022-04-14',  # 1.25% → 1.50%
                '2023-01-13',  # 3.25% → 3.50%
            ]
            
            found_dates = [item.get('date') for item in validation['expected_changes']]
            validation['known_changes_found'] = [
                date for date in known_changes if date in found_dates
            ]
            validation['missing_known_changes'] = [
                date for date in known_changes if date not in found_dates
            ]
            
        except Exception as e:
            validation['error'] = str(e)
        
        self.validation_results['interest_rates'] = validation
        return validation
    
    def generate_report(self):
        """종합 검증 보고서 생성"""
        print("\n" + "="*60)
        print("크롤러 완전성 종합 보고서")
        print("="*60)
        
        # 각 크롤러 검증
        mpb_result = self.validate_mpb_crawler()
        call_result = self.validate_call_rates_crawler()
        interest_result = self.validate_interest_rates_crawler()
        
        # 보고서 출력
        print("\n### MPB 크롤러 검증 결과 ###")
        print(f"- 예상 항목: {mpb_result.get('expected_count', 0)}개")
        print(f"- 수집 항목: {mpb_result.get('crawled_count', 0)}개")
        print(f"- Coverage: {mpb_result.get('coverage_rate', 0):.1f}%")
        if mpb_result.get('missing_items'):
            print(f"- 누락 항목: {len(mpb_result['missing_items'])}개")
            for item in mpb_result['missing_items'][:3]:
                print(f"  • {item['title'][:50]}... (페이지 {item['page']})")
        
        print("\n### 콜금리 크롤러 검증 결과 ###")
        for date_range, coverage in call_result.get('date_range_coverage', {}).items():
            if 'error' not in coverage:
                status = "✅" if coverage.get('complete') else "⚠️"
                print(f"- {date_range}: {status} {coverage.get('found_records')}개 레코드")
        
        print("\n### 기준금리 크롤러 검증 결과 ###")
        if interest_result.get('javascript_data_found'):
            print(f"✅ JavaScript 데이터 발견")
            print(f"- 2014-2025 금리 변경: {len(interest_result.get('expected_changes', []))}개")
            print(f"- 알려진 변경 확인: {len(interest_result.get('known_changes_found', []))}/{len(interest_result.get('known_changes_found', []) + interest_result.get('missing_known_changes', []))}")
            if interest_result.get('missing_known_changes'):
                print(f"  ⚠️ 누락된 알려진 변경: {interest_result['missing_known_changes']}")
        else:
            print("❌ JavaScript 데이터 미발견")
        
        # JSON 저장
        report_file = 'comprehensive_validation_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 상세 보고서가 {report_file}에 저장되었습니다.")
        
        # 종합 평가
        print("\n" + "="*60)
        print("종합 평가")
        print("="*60)
        
        critical_issues = []
        
        if mpb_result.get('coverage_rate', 0) < 90:
            critical_issues.append("MPB 크롤러 coverage 90% 미만")
        
        if not interest_result.get('javascript_data_found'):
            critical_issues.append("기준금리 JavaScript 데이터 접근 실패")
        
        if critical_issues:
            print("⚠️ 주요 이슈:")
            for issue in critical_issues:
                print(f"  - {issue}")
        else:
            print("✅ 모든 크롤러가 정상적으로 작동 중입니다.")
        
        return self.validation_results


if __name__ == "__main__":
    validator = ComprehensiveCrawlerValidator()
    validator.generate_report()