import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

def research_yonhap_historical_access():
    """Research Yonhap's historical article access methods for 10-year data collection"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    print("🔍 연합뉴스 과거 기사 접근 방법 연구")
    print("=" * 50)
    
    # 1. 기본 검색 URL 분석 (다양한 날짜 범위)
    test_dates = [
        ("2025-01-01", "2025-08-18"),  # 최근
        ("2024-01-01", "2024-12-31"),  # 1년 전
        ("2023-01-01", "2023-12-31"),  # 2년 전
        ("2020-01-01", "2020-12-31"),  # 5년 전
        ("2015-01-01", "2015-12-31"),  # 10년 전
    ]
    
    for start_date, end_date in test_dates:
        print(f"\n📅 테스트 기간: {start_date} ~ {end_date}")
        
        # 다양한 검색 URL 패턴 시도
        search_patterns = [
            # 패턴 1: 기본 검색
            f"https://www.yna.co.kr/search?query=금리&sort=date&period=range&start={start_date}&end={end_date}",
            # 패턴 2: 고급 검색
            f"https://www.yna.co.kr/advanced-search?keyword=금리&from={start_date}&to={end_date}",
            # 패턴 3: API 스타일
            f"https://www.yna.co.kr/api/search?q=금리&startDate={start_date}&endDate={end_date}",
            # 패턴 4: 아카이브
            f"https://www.yna.co.kr/archive/search?keyword=금리&start={start_date}&end={end_date}",
        ]
        
        for i, url in enumerate(search_patterns, 1):
            try:
                print(f"   패턴 {i}: {url[:80]}...")
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # 검색 결과 확인
                    article_links = soup.find_all('a', href=True)
                    article_count = len([link for link in article_links if '/view/' in link.get('href', '')])
                    
                    print(f"      ✅ 응답 성공 (200) - 기사 링크 {article_count}개 발견")
                    
                    # 페이지네이션 확인
                    pagination = soup.find_all(['div', 'ul'], class_=['pagination', 'paging', 'page'])
                    if pagination:
                        print(f"      📄 페이지네이션 발견: {len(pagination)}개")
                    
                elif response.status_code == 404:
                    print(f"      ❌ 404 - URL 존재하지 않음")
                elif response.status_code == 403:
                    print(f"      🚫 403 - 접근 금지")
                else:
                    print(f"      ⚠️ {response.status_code} - 기타 응답")
                    
            except Exception as e:
                print(f"      💥 에러: {e}")
            
            time.sleep(1)  # 요청 간격
    
    print("\n" + "=" * 50)
    print("🔍 대안 접근 방법 연구")
    
    # 2. 섹션별 아카이브 접근 연구
    sections = [
        "/economy/finance",
        "/economy/market", 
        "/economy/bank",
        "/politics/economyPolicy"
    ]
    
    for section in sections:
        print(f"\n📂 섹션: {section}")
        
        # 과거 날짜별 접근 시도
        test_years = [2025, 2024, 2023, 2020, 2015]
        
        for year in test_years:
            archive_urls = [
                f"https://www.yna.co.kr{section}?year={year}",
                f"https://www.yna.co.kr{section}/{year}",
                f"https://www.yna.co.kr/archive{section}?year={year}",
            ]
            
            for url in archive_urls:
                try:
                    response = requests.get(url, headers=headers, timeout=5)
                    if response.status_code == 200:
                        print(f"   ✅ {year}년 접근 가능: {url}")
                        break
                except:
                    continue
            else:
                print(f"   ❌ {year}년 접근 불가")
            
            time.sleep(0.5)
    
    print("\n" + "=" * 50)
    print("🔍 sitemap 및 robots.txt 분석")
    
    # 3. sitemap 분석
    sitemap_urls = [
        "https://www.yna.co.kr/sitemap.xml",
        "https://www.yna.co.kr/sitemap/news.xml",
        "https://www.yna.co.kr/robots.txt",
    ]
    
    for url in sitemap_urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"✅ {url} 접근 가능")
                if 'sitemap' in url:
                    # sitemap 내용 분석
                    content = response.text
                    if '2015' in content or '2016' in content:
                        print("   📅 2015-2016년 데이터 포함 가능성 있음")
                    if '<loc>' in content:
                        urls_count = content.count('<loc>')
                        print(f"   📊 총 {urls_count}개 URL 포함")
            else:
                print(f"❌ {url} 접근 불가 ({response.status_code})")
        except Exception as e:
            print(f"💥 {url} 에러: {e}")

if __name__ == "__main__":
    research_yonhap_historical_access()