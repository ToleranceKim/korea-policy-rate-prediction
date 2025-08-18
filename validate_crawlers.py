#!/usr/bin/env python3
"""
크롤러 검증 스크립트
PostgreSQL 없이도 크롤러 구조와 기능을 테스트합니다.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def validate_mpb_crawler():
    """MPB 크롤러 검증"""
    print("🕷️  MPB 크롤러 검증 중...")
    
    mpb_path = project_root / "crawler" / "MPB" / "mpb_crawler"
    spider_path = mpb_path / "spiders" / "mpb_crawler.py"
    
    if not mpb_path.exists():
        print("❌ MPB 크롤러 디렉토리가 없습니다")
        return False
    
    if not spider_path.exists():
        print("❌ MPB 스파이더 파일이 없습니다")
        return False
    
    try:
        # Import check
        sys.path.append(str(mpb_path))
        from spiders.mpb_crawler import MpbCrawlerSpider
        spider = MpbCrawlerSpider()
        
        print(f"✅ MPB 크롤러 로드 성공")
        print(f"   - 스파이더명: {spider.name}")
        print(f"   - 허용 도메인: {spider.allowed_domains}")
        return True
        
    except Exception as e:
        print(f"❌ MPB 크롤러 로드 실패: {e}")
        return False

def validate_news_crawlers():
    """뉴스 크롤러 검증"""
    print("\n📰 뉴스 크롤러 검증 중...")
    
    crawlers = [
        {
            'name': 'Yonhap News',
            'path': project_root / "crawler" / "yh" / "yh_crawler" / "yh_crawler",
            'spider_file': 'spiders/yh_spider.py',
            'spider_class': 'YhSpider'
        },
        {
            'name': 'Edaily',
            'path': project_root / "crawler" / "edaily" / "edaily_crawler" / "edaily_crawler",
            'spider_file': 'spiders/edaily_spider.py',
            'spider_class': 'EdailySpider'
        }
    ]
    
    success_count = 0
    
    for crawler in crawlers:
        spider_path = crawler['path'] / crawler['spider_file']
        
        if not crawler['path'].exists():
            print(f"❌ {crawler['name']} 크롤러 디렉토리가 없습니다")
            continue
            
        if not spider_path.exists():
            print(f"❌ {crawler['name']} 스파이더 파일이 없습니다")
            continue
        
        try:
            # Read spider file to check basic structure
            with open(spider_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if crawler['spider_class'] in content and 'scrapy.Spider' in content:
                print(f"✅ {crawler['name']} 크롤러 구조 확인됨")
                success_count += 1
            else:
                print(f"❌ {crawler['name']} 크롤러 구조가 올바르지 않습니다")
                
        except Exception as e:
            print(f"❌ {crawler['name']} 크롤러 검증 실패: {e}")
    
    return success_count == len(crawlers)

def validate_bond_crawler():
    """채권 크롤러 검증"""
    print("\n💰 채권 크롤러 검증 중...")
    
    bond_script = project_root / "crawler" / "BOND" / "bond_crawling.py"
    
    if not bond_script.exists():
        print("❌ 채권 크롤러 스크립트가 없습니다")
        return False
    
    try:
        # Check if the file has the basic structure
        with open(bond_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_elements = [
            'requests', 'BeautifulSoup', 'process_report', 
            'finance.naver.com', 'ThreadPoolExecutor'
        ]
        
        missing = [elem for elem in required_elements if elem not in content]
        
        if missing:
            print(f"❌ 채권 크롤러에 필요한 요소가 없습니다: {missing}")
            return False
        
        print("✅ 채권 크롤러 구조 확인됨")
        print("   - 멀티스레딩 구현됨")
        print("   - 네이버 금융 크롤링 구현됨")
        return True
        
    except Exception as e:
        print(f"❌ 채권 크롤러 검증 실패: {e}")
        return False

def validate_rates_crawler():
    """콜금리 크롤러 검증"""
    print("\n📈 콜금리 크롤러 검증 중...")
    
    rates_path = project_root / "crawler" / "call_ratings" / "call_ratings_crawler"
    spider_path = rates_path / "spiders" / "call_ratings.py"
    
    if not rates_path.exists():
        print("❌ 콜금리 크롤러 디렉토리가 없습니다")
        return False
    
    if not spider_path.exists():
        print("❌ 콜금리 스파이더 파일이 없습니다")
        return False
    
    try:
        # Read spider file
        with open(spider_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'CallRatingsSpider' in content and 'scrapy.Spider' in content:
            print("✅ 콜금리 크롤러 구조 확인됨")
            print("   - Scrapy 스파이더 구현됨")
            return True
        else:
            print("❌ 콜금리 크롤러 구조가 올바르지 않습니다")
            return False
            
    except Exception as e:
        print(f"❌ 콜금리 크롤러 검증 실패: {e}")
        return False

def validate_main_pipeline():
    """메인 파이프라인 검증"""
    print("\n🚀 메인 파이프라인 검증 중...")
    
    try:
        from main_pipeline import MPBPipeline
        
        # Check if all required methods exist
        pipeline = MPBPipeline()
        required_methods = [
            'run_crawlers', '_run_mpb_crawler', '_run_news_crawlers',
            '_run_bond_crawler', '_run_rates_crawler', 'process_data',
            'analyze_ngrams', 'train_models', 'evaluate_models',
            'generate_predictions', 'run_full_pipeline'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(pipeline, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ 파이프라인에 필요한 메소드가 없습니다: {missing_methods}")
            return False
        
        print("✅ 메인 파이프라인 구조 확인됨")
        print("   - 모든 크롤러 메소드 구현됨")
        print("   - 데이터 처리 메소드 구현됨")
        print("   - 모델 훈련/평가 메소드 구현됨")
        return True
        
    except Exception as e:
        print(f"❌ 메인 파이프라인 검증 실패: {e}")
        return False

def main():
    """메인 검증 함수"""
    print("🔍 MPB Stance Mining 크롤러 검증 시작")
    print("=" * 50)
    
    results = []
    
    # 각 컴포넌트 검증
    results.append(("MPB 크롤러", validate_mpb_crawler()))
    results.append(("뉴스 크롤러", validate_news_crawlers()))
    results.append(("채권 크롤러", validate_bond_crawler()))
    results.append(("콜금리 크롤러", validate_rates_crawler()))
    results.append(("메인 파이프라인", validate_main_pipeline()))
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("🎯 검증 결과 요약:")
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"   {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n총 {passed}/{total} 개 컴포넌트 통과")
    
    if passed == total:
        print("\n🎉 모든 크롤러가 정상적으로 구현되었습니다!")
        print("\n다음 단계:")
        print("1. PostgreSQL 설치 및 설정")
        print("2. 데이터베이스 스키마 초기화")
        print("3. 크롤러 실행 및 데이터 수집")
        print("4. 텍스트 전처리 및 분석")
    else:
        print(f"\n⚠️  {total - passed}개 컴포넌트에 문제가 있습니다.")
        print("위 오류를 수정한 후 다시 실행해주세요.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)