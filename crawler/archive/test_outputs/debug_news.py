#!/usr/bin/env python3
"""
Debug script to analyze news website structure
"""
import requests
from bs4 import BeautifulSoup
import time

def analyze_yonhap():
    """Analyze Yonhap news search structure"""
    print("=== Analyzing Yonhap News ===")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
    }
    
    # Try simple search
    url = "https://www.yna.co.kr/search?query=금리&sort=1&period=all&page=1"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Length: {len(response.text)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find search results container
            search_containers = soup.find_all('div', class_=True)
            print(f"\nFound {len(search_containers)} div elements with classes")
            
            # Look for article links
            links = soup.find_all('a', href=True)
            article_links = [link for link in links if '/view/' in link.get('href', '')]
            print(f"Found {len(article_links)} potential article links")
            
            if article_links:
                print("Sample article links:")
                for link in article_links[:3]:
                    print(f"  - {link.get('href')} | {link.get_text().strip()[:50]}")
            
            # Look for pagination
            pagination = soup.find_all(['div', 'ul', 'span'], class_=lambda x: x and 'page' in x.lower() if x else False)
            print(f"Found {len(pagination)} potential pagination elements")
            
    except Exception as e:
        print(f"Error accessing Yonhap: {e}")

def analyze_edaily():
    """Analyze Edaily search structure"""
    print("\n=== Analyzing Edaily ===")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    url = "https://www.edaily.co.kr/search/news?keyword=금리&newsType=title_content&period=all&page=1"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Length: {len(response.text)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Save HTML for analysis
            with open('/tmp/edaily_debug.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
                
            # Look for search results
            search_results = soup.find_all('div', class_=lambda x: x and 'search' in x.lower() if x else False)
            print(f"Found {len(search_results)} search result containers")
            
            # Look for article titles/links
            links = soup.find_all('a', href=True)
            news_links = [link for link in links if '/news/read' in link.get('href', '')]
            print(f"Found {len(news_links)} news article links")
            
            if news_links:
                print("Sample news links:")
                for link in news_links[:3]:
                    print(f"  - {link.get('href')} | {link.get_text().strip()[:50]}")
            
            # Look for article containers
            article_containers = soup.find_all('div', class_=lambda x: x and ('article' in x.lower() or 'news' in x.lower()) if x else False)
            print(f"Found {len(article_containers)} potential article containers")
            
            # Check for all possible news-related selectors
            selectors_to_test = [
                'div.newsbox_01 dl dt a',
                'div.newsbox_02 dl dt a',
                'div.newsbox_03 dl dt a', 
                'div.newsbox_04 dl dt a',
                'div.newsbox_04 a',
                'div.news_list li h4 a', 
                'div.search_result a',
                'div.list_news_title a',
                '.search_news_list a',
                'a[href*="/News/Read"]',
                'div[class*="newsbox"] a'
            ]
            
            for selector in selectors_to_test:
                elements = soup.select(selector)
                print(f"Selector '{selector}': {len(elements)} elements")
                if elements and len(elements) > 0:
                    print(f"  Sample element: {elements[0].get('href')} | {elements[0].get_text().strip()[:50]}")
            
            # Check all div classes to understand structure
            all_divs = soup.find_all('div', class_=True)
            div_classes = {}
            for div in all_divs:
                classes = div.get('class')
                if classes:
                    for cls in classes:
                        if 'news' in cls.lower() or 'box' in cls.lower() or 'search' in cls.lower():
                            div_classes[cls] = div_classes.get(cls, 0) + 1
            
            print(f"\nRelevant div classes found:")
            for cls, count in sorted(div_classes.items()):
                print(f"  {cls}: {count} occurrences")
                
            # Also sample individual article page content
            news_links = [link for link in soup.find_all('a', href=True) if '/News/Read' in link.get('href', '')]
            if news_links:
                print(f"\nTesting article content extraction from first article...")
                article_url = news_links[0].get('href')
                if not article_url.startswith('http'):
                    article_url = 'https://www.edaily.co.kr' + article_url
                
                try:
                    article_response = requests.get(article_url, headers=headers, timeout=10)
                    if article_response.status_code == 200:
                        article_soup = BeautifulSoup(article_response.text, 'html.parser')
                        
                        # Test content selectors
                        content_selectors = [
                            'div.news_body p',
                            'div.ArticleView p',
                            'div.article_content p',
                            'div[class*="content"] p',
                            'div[class*="body"] p'
                        ]
                        
                        for selector in content_selectors:
                            content_elements = article_soup.select(selector)
                            if content_elements:
                                content_text = ' '.join([p.get_text().strip() for p in content_elements[:3]])
                                print(f"  Content selector '{selector}': {len(content_elements)} elements")
                                print(f"    Sample: {content_text[:100]}...")
                                break
                        else:
                            # Get all p tags as fallback
                            all_p = article_soup.find_all('p')
                            print(f"  Found {len(all_p)} total p tags in article")
                            for p in all_p[:5]:
                                text = p.get_text().strip()
                                if text and len(text) > 20:
                                    print(f"    P tag: {text[:80]}...")
                            
                except Exception as e:
                    print(f"  Error accessing article: {e}")
                
    except Exception as e:
        print(f"Error accessing Edaily: {e}")

if __name__ == "__main__":
    analyze_yonhap()
    time.sleep(2)
    analyze_edaily()