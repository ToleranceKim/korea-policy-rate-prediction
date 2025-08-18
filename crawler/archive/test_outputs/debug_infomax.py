#!/usr/bin/env python3
"""
Debug script to analyze InfoMax article structure
"""
import requests
from bs4 import BeautifulSoup

def analyze_infomax_article():
    """Analyze InfoMax article structure"""
    print("=== Analyzing InfoMax Article ===")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://news.einfomax.co.kr/'
    }
    
    # Test article URL (from the crawler logs)
    test_url = "https://news.einfomax.co.kr/news/articleView.html?idxno=4369275"
    
    print(f"Testing article: {test_url}")
    
    try:
        response = requests.get(test_url, headers=headers, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Response Length: {len(response.text)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Save HTML for manual analysis
            with open('/tmp/infomax_article_debug.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("HTML saved to /tmp/infomax_article_debug.html")
            
            # Test title selectors
            print("\n=== Testing Title Selectors ===")
            title_selectors = [
                'h3.heading',
                'h1.heading',
                'div.article-head h1',
                'h1',
                'h2', 
                'h3'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    print(f"Title found with '{selector}': {title_elem.get_text().strip()}")
                    break
            else:
                print("No title found with any selector")
            
            # Test content selectors
            print("\n=== Testing Content Selectors ===")
            content_selectors = [
                '#article-view-content-div',
                'div.article-view-content-div',
                'div[id*="content"]',
                'div[class*="content"]',
                'div.article-content',
                'div.news-content',
                'article',
                'main'
            ]
            
            found_content = False
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    content_text = content_div.get_text().strip()
                    if len(content_text) > 100:
                        print(f"Content found with '{selector}':")
                        print(f"  Length: {len(content_text)}")
                        print(f"  Preview: {content_text[:200]}...")
                        found_content = True
                        break
            
            if not found_content:
                print("No substantial content found with standard selectors")
                
                # Try to find all divs with substantial text
                print("\n=== Analyzing All Divs ===")
                all_divs = soup.find_all('div')
                for i, div in enumerate(all_divs):
                    text = div.get_text().strip()
                    if len(text) > 200 and '금리' in text:
                        classes = div.get('class', [])
                        div_id = div.get('id', '')
                        print(f"Div {i}: id={div_id}, classes={classes}, length={len(text)}")
                        print(f"  Preview: {text[:150]}...")
            
            # Test date selectors
            print("\n=== Testing Date Selectors ===")
            date_selectors = [
                'ul.infomation li',
                'ul.information li',
                'div.article-info',
                'div.news-info',
                'p.date',
                'span.date'
            ]
            
            for selector in date_selectors:
                date_elements = soup.select(selector)
                if date_elements:
                    print(f"Date elements found with '{selector}':")
                    for elem in date_elements[:3]:
                        text = elem.get_text().strip()
                        if text:
                            print(f"  - {text}")
                    break
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_infomax_article()