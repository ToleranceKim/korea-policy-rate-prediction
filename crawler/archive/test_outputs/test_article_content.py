#!/usr/bin/env python3
"""
Test script to analyze individual article page structure and extract content properly
"""
import requests
from bs4 import BeautifulSoup
import time

def test_single_article():
    """Test content extraction from a specific article"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    # Test with a specific 금리 related article
    test_url = "https://www.edaily.co.kr/News/Read?newsId=03414486642268632&mediaCodeNo=257"
    
    print(f"Testing article: {test_url}")
    
    try:
        response = requests.get(test_url, headers=headers, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Response Length: {len(response.text)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Save HTML for manual analysis
            with open('/tmp/edaily_article_debug.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("HTML saved to /tmp/edaily_article_debug.html")
            
            # Find title
            title_selectors = [
                'div.news_titles h1',
                'h1.news_title', 
                'div.article_head h1',
                'h1',
                'div[class*="title"] h1',
                'div[class*="head"] h1'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    print(f"Title found with '{selector}': {title_elem.get_text().strip()}")
                    break
            else:
                print("No title found")
            
            # Find article content in various ways
            print("\n=== Testing Content Selectors ===")
            
            content_selectors = [
                'div.news_body',
                'div.ArticleView', 
                'div.article_content',
                'div[class*="content"]',
                'div[class*="body"]',
                'div[class*="text"]',
                'article',
                'main'
            ]
            
            found_content = False
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    # Get all text content
                    text_content = content_div.get_text().strip()
                    if len(text_content) > 100:  # Substantial content
                        print(f"Content found with '{selector}':")
                        print(f"  Length: {len(text_content)}")
                        print(f"  Preview: {text_content[:200]}...")
                        
                        # Also get paragraphs within this div
                        paragraphs = content_div.find_all('p')
                        print(f"  Paragraphs found: {len(paragraphs)}")
                        found_content = True
                        break
            
            if not found_content:
                print("No substantial content found with standard selectors")
                
                # Try to find all divs with substantial text
                print("\n=== Analyzing All Divs ===")
                all_divs = soup.find_all('div')
                for i, div in enumerate(all_divs):
                    text = div.get_text().strip()
                    if len(text) > 200 and '금리' in text:  # Substantial content with our keyword
                        classes = div.get('class', [])
                        print(f"Div {i}: classes={classes}, length={len(text)}")
                        print(f"  Preview: {text[:150]}...")
                        
            # Check for any script tags that might contain article data
            print("\n=== Checking Script Tags ===")
            scripts = soup.find_all('script')
            for script in scripts:
                script_content = script.get_text()
                if '금리' in script_content and len(script_content) > 100:
                    print(f"Script with 금리 content found: {len(script_content)} chars")
                    print(f"  Preview: {script_content[:100]}...")
            
            # Check for JSON-LD structured data
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            print(f"Found {len(json_ld_scripts)} JSON-LD scripts")
            for script in json_ld_scripts:
                print(f"  JSON-LD content preview: {script.get_text()[:100]}...")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_single_article()