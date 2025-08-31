#!/usr/bin/env python3
"""
2024년 MPB 의사록 찾기
"""

import requests
from bs4 import BeautifulSoup
import re
import time

def find_2024_mpb():
    """2024년 의사록 찾기"""
    url = 'https://www.bok.or.kr/portal/singl/newsData/listCont.do'
    
    print("2024년 MPB 의사록 검색 중...")
    print("="*60)
    
    found_2024 = []
    pages_checked = 0
    
    # 이진 탐색으로 2024년 위치 찾기
    # 최신순이므로 2024년은 중간쯤에 있을 것
    for page in [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
        params = {
            'targetDepth': 4,
            'menuNo': 200789,
            'pageIndex': page
        }
        
        response = requests.get(url, params=params)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        items = soup.select('li.bbsRowCls')
        pages_checked += 1
        
        years_on_page = []
        
        for item in items:
            title_elem = item.select_one('a.title')
            if title_elem:
                title = title_elem.get_text(strip=True)
                
                # 날짜를 title에서 추출하거나 item 전체 텍스트에서 추출
                item_text = item.get_text()
                
                # 여러 날짜 패턴 시도
                patterns = [
                    r'(\d{4})[\.년\s]+(\d{1,2})[\.월\s]+(\d{1,2})',
                    r'(\d{4})\.(\d{2})\.(\d{2})',
                    r'(\d{4})-(\d{2})-(\d{2})'
                ]
                
                for pattern in patterns:
                    date_match = re.search(pattern, item_text)
                    if date_match:
                        year = int(date_match.group(1))
                        years_on_page.append(year)
                        
                        if year == 2024:
                            found_2024.append({
                                'page': page,
                                'title': title,
                                'date': date_match.group()
                            })
                            print(f"✅ 페이지 {page}: {title}")
                        break
        
        if years_on_page:
            min_year = min(years_on_page)
            max_year = max(years_on_page)
            print(f"페이지 {page}: {min_year}년 ~ {max_year}년")
        
        time.sleep(0.5)  # 서버 부담 방지
    
    print(f"\n검색 완료: {pages_checked}페이지 확인")
    print(f"2024년 의사록: {len(found_2024)}개 발견")
    
    # 정확한 페이지 범위 찾기
    if found_2024:
        min_page = min(item['page'] for item in found_2024)
        max_page = max(item['page'] for item in found_2024)
        print(f"2024년 의사록 페이지 범위: {min_page} ~ {max_page}")
        
        # 해당 범위 정밀 검색
        print("\n정밀 검색 시작...")
        total_2024 = 0
        
        for page in range(min_page - 5, max_page + 5):
            params['pageIndex'] = page
            response = requests.get(url, params=params)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            items = soup.select('li.bbsRowCls')
            for item in items:
                item_text = item.get_text()
                date_match = re.search(r'(\d{4})[\.년\s]+(\d{1,2})[\.월\s]+(\d{1,2})', item_text)
                if date_match and int(date_match.group(1)) == 2024:
                    total_2024 += 1
            
            time.sleep(0.3)
        
        print(f"\n총 2024년 의사록: {total_2024}개")

if __name__ == "__main__":
    find_2024_mpb()