#!/usr/bin/env python3
"""
완전한 데이터 수집 검증 스크립트
모든 크롤러가 전체 데이터를 수집하는지 검증
"""

import os
import sys
import subprocess
import json
import csv
import time
from pathlib import Path
from datetime import datetime


class CompleteDataVerifier:
    """전체 데이터 수집 검증기"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.test_dir = self.base_dir / 'test_outputs'
        self.test_dir.mkdir(exist_ok=True)
        
        self.results = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def test_mpb_complete(self):
        """MPB 의사록 완전 수집 검증"""
        print("\n" + "="*60)
        print("MPB 의사록 크롤러 검증 (전체 547개)")
        print("="*60)
        
        mpb_dir = self.base_dir / 'MPB' / 'mpb_crawler'
        os.chdir(mpb_dir)
        
        output_file = self.test_dir / f'mpb_complete_{self.timestamp}.json'
        
        cmd = [
            'scrapy', 'crawl', 'mpb_crawler_perfect',
            '-a', 'start_year=2014',
            '-a', 'end_year=2025',
            '-o', str(output_file),
            '-L', 'INFO'
        ]
        
        print(f"실행 명령: {' '.join(cmd)}")
        print("크롤링 중... (약 5-10분 소요)")
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        elapsed = time.time() - start_time
        
        if result.returncode == 0 and output_file.exists():
            with open(output_file) as f:
                data = json.load(f)
            
            print(f"\n✅ 크롤링 완료: {len(data)}개 수집 ({elapsed:.1f}초)")
            
            # 목표 대비 달성률
            target = 547  # 실제 웹사이트 기준
            achievement = (len(data) / target) * 100
            
            # 연도별 분포
            year_dist = {}
            for item in data:
                if item.get('year'):
                    year = str(item['year'])
                    year_dist[year] = year_dist.get(year, 0) + 1
            
            print(f"📊 목표 달성률: {achievement:.1f}% ({len(data)}/{target})")
            print("📅 연도별 분포:")
            for year in sorted(year_dist.keys()):
                print(f"   {year}: {year_dist[year]}개")
            
            # PDF 추출 성공률
            success_count = sum(1 for item in data if item.get('content'))
            print(f"📄 PDF 추출 성공: {success_count}/{len(data)} ({(success_count/len(data)*100):.1f}%)")
            
            self.results['mpb'] = {
                'status': 'COMPLETE' if achievement >= 95 else 'PARTIAL',
                'total': len(data),
                'target': target,
                'achievement': achievement,
                'years': year_dist
            }
            
            if achievement < 95:
                print(f"⚠️ 경고: 목표 달성률이 95% 미만입니다!")
                
        else:
            print(f"❌ 크롤링 실패: {result.stderr[:500] if result.stderr else 'Unknown error'}")
            self.results['mpb'] = {'status': 'FAILED'}
    
    def test_call_rates_complete(self):
        """콜금리 완전 수집 검증"""
        print("\n" + "="*60)
        print("콜금리 크롤러 검증 (전체 2,866개)")
        print("="*60)
        
        call_dir = self.base_dir / 'call_ratings' / 'call_ratings_crawler'
        os.chdir(call_dir)
        
        output_file = self.test_dir / f'call_rates_complete_{self.timestamp}.csv'
        
        cmd = [
            'scrapy', 'crawl', 'call_ratings_complete',
            '-a', 'start_date=2014-01-01',
            '-a', 'end_date=2025-12-31',
            '-o', str(output_file),
            '-L', 'INFO'
        ]
        
        print(f"실행 명령: {' '.join(cmd)}")
        print("크롤링 중... (약 3-5분 소요)")
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        elapsed = time.time() - start_time
        
        if result.returncode == 0 and output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
            
            print(f"\n✅ 크롤링 완료: {len(data)}개 수집 ({elapsed:.1f}초)")
            
            # 목표 대비 달성률
            target = 2866  # 실제 웹사이트 기준
            achievement = (len(data) / target) * 100
            
            # 날짜 범위 확인
            dates = [row.get('날짜') for row in data if row.get('날짜')]
            if dates:
                print(f"📊 목표 달성률: {achievement:.1f}% ({len(data)}/{target})")
                print(f"📅 날짜 범위: {min(dates)} ~ {max(dates)}")
                print(f"📈 고유 날짜: {len(set(dates))}개")
            
            self.results['call_rates'] = {
                'status': 'COMPLETE' if achievement >= 95 else 'PARTIAL',
                'total': len(data),
                'target': target,
                'achievement': achievement,
                'date_range': f"{min(dates)} ~ {max(dates)}" if dates else None
            }
            
            if achievement < 95:
                print(f"⚠️ 경고: 목표 달성률이 95% 미만입니다!")
                
        else:
            print(f"❌ 크롤링 실패: {result.stderr[:500] if result.stderr else 'Unknown error'}")
            self.results['call_rates'] = {'status': 'FAILED'}
    
    def test_interest_rates_complete(self):
        """기준금리 완전 수집 검증"""
        print("\n" + "="*60)
        print("기준금리 크롤러 검증 (전체 20개 변경)")
        print("="*60)
        
        rates_dir = self.base_dir / 'interest_rates' / 'interest_rates_crawler'
        os.chdir(rates_dir)
        
        output_file = self.test_dir / f'interest_rates_complete_{self.timestamp}.csv'
        
        cmd = [
            'scrapy', 'crawl', 'interest_rates_complete',
            '-a', 'start_year=2014',
            '-a', 'end_year=2025',
            '-o', str(output_file),
            '-L', 'INFO'
        ]
        
        print(f"실행 명령: {' '.join(cmd)}")
        print("크롤링 중...")
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        elapsed = time.time() - start_time
        
        if result.returncode == 0 and output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
            
            print(f"\n✅ 크롤링 완료: {len(data)}개 수집 ({elapsed:.1f}초)")
            
            # 목표 대비 달성률
            target = 20  # 2014-2025년 기준금리 변경 횟수
            achievement = (len(data) / target) * 100
            
            # 금리 변경 내역
            rates = []
            for row in data:
                if row.get('기준금리'):
                    rate_str = row['기준금리'].replace('%', '').strip()
                    try:
                        rates.append(float(rate_str))
                    except:
                        pass
            
            print(f"📊 목표 달성률: {achievement:.1f}% ({len(data)}/{target})")
            if rates:
                print(f"📈 금리 범위: {min(rates):.2f}% ~ {max(rates):.2f}%")
                print(f"🎯 변경 횟수: {len(data)}회")
            
            self.results['interest_rates'] = {
                'status': 'COMPLETE' if len(data) >= 15 else 'PARTIAL',
                'total': len(data),
                'target': target,
                'achievement': achievement,
                'rate_range': f"{min(rates):.2f}% ~ {max(rates):.2f}%" if rates else None
            }
            
            if len(data) < 15:
                print(f"⚠️ 경고: 예상보다 적은 데이터입니다!")
                
        else:
            print(f"❌ 크롤링 실패: {result.stderr[:500] if result.stderr else 'Unknown error'}")
            self.results['interest_rates'] = {'status': 'FAILED'}
    
    def print_final_report(self):
        """최종 검증 보고서"""
        print("\n" + "#"*60)
        print("전체 데이터 수집 검증 보고서")
        print("#"*60)
        
        print("\n📋 크롤러별 상태:")
        print("-"*50)
        
        all_complete = True
        
        for name, result in self.results.items():
            status = result.get('status', 'NOT_TESTED')
            
            if name == 'mpb':
                display_name = "MPB 의사록"
            elif name == 'call_rates':
                display_name = "콜금리"
            elif name == 'interest_rates':
                display_name = "기준금리"
            else:
                display_name = name
            
            if status == 'COMPLETE':
                achievement = result.get('achievement', 100)
                print(f"✅ {display_name:15} : 완전 수집 ({achievement:.1f}%)")
                print(f"   └─ 수집: {result['total']:,}개 / 목표: {result['target']:,}개")
            elif status == 'PARTIAL':
                achievement = result.get('achievement', 0)
                all_complete = False
                print(f"⚠️ {display_name:15} : 부분 수집 ({achievement:.1f}%)")
                print(f"   └─ 수집: {result['total']:,}개 / 목표: {result['target']:,}개")
                print(f"   └─ 누락: {result['target'] - result['total']:,}개")
            else:
                all_complete = False
                print(f"❌ {display_name:15} : 실패")
        
        print("\n" + "="*50)
        if all_complete:
            print("🎉 모든 크롤러가 전체 데이터를 성공적으로 수집했습니다!")
        else:
            print("⚠️ 일부 크롤러에서 데이터 누락이 발생했습니다.")
            print("\n권장 조치:")
            for name, result in self.results.items():
                if result.get('status') != 'COMPLETE':
                    print(f"  - {name}: 페이지네이션 로직 재확인 필요")
        
        # 결과 저장
        report_file = self.test_dir / f'verification_report_{self.timestamp}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n📁 상세 보고서 저장: {report_file}")
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("\n" + "="*60)
        print("전체 데이터 수집 검증 시작")
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # 각 크롤러 테스트
        tests = [
            ('MPB 의사록', self.test_mpb_complete),
            ('콜금리', self.test_call_rates_complete),
            ('기준금리', self.test_interest_rates_complete)
        ]
        
        for name, test_func in tests:
            try:
                test_func()
            except subprocess.TimeoutExpired:
                print(f"⏱️ {name} 테스트 시간 초과")
                self.results[name.lower().replace(' ', '_')] = {'status': 'TIMEOUT'}
            except Exception as e:
                print(f"❌ {name} 테스트 오류: {e}")
                self.results[name.lower().replace(' ', '_')] = {'status': 'ERROR', 'error': str(e)}
        
        # 최종 보고서
        self.print_final_report()


def main():
    """메인 실행"""
    verifier = CompleteDataVerifier()
    
    print("전체 데이터 수집 검증을 시작합니다.")
    print("예상 소요 시간: 약 10-20분")
    print("\n주의: 이 스크립트는 실제 웹사이트에서 모든 데이터를 수집합니다.")
    print("네트워크 상태에 따라 시간이 더 걸릴 수 있습니다.")
    
    response = input("\n계속하시겠습니까? (y/n): ")
    if response.lower() != 'y':
        print("취소되었습니다.")
        return
    
    verifier.run_all_tests()


if __name__ == "__main__":
    main()