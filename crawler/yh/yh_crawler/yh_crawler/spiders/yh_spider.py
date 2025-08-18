import scrapy
import re
from datetime import datetime, timedelta


class YhSpider(scrapy.Spider):
    name = "yh_spider"
    allowed_domains = ["yna.co.kr"]
    
    def start_requests(self):
        """Generate requests for financial news from Yonhap"""
        # Search for financial/monetary policy related keywords
        keywords = [
            "금리", "기준금리", "통화정책", "금융통화위원회", "한국은행", 
            "콜금리", "금통위", "기준금리", "통화정책방향"
        ]
        
        base_url = "https://www.yna.co.kr/search"
        
        # Search for articles from the last 5 years
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*5)
        
        for keyword in keywords:
            for page in range(1, 51):  # Limit to 50 pages per keyword
                params = {
                    'query': keyword,
                    'sort': '1',  # Sort by date
                    'period': 'all',
                    'page': page
                }
                
                url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
                yield scrapy.Request(
                    url=url, 
                    callback=self.parse, 
                    meta={'keyword': keyword, 'page': page}
                )
    
    def parse(self, response):
        """Parse search results and extract article links"""
        # Extract article links from search results
        article_links = response.css('div.list-type038 li dt a::attr(href)').getall()
        
        for link in article_links:
            if link and not link.startswith('http'):
                link = 'https://www.yna.co.kr' + link
            
            yield response.follow(link, self.parse_article, meta={
                'keyword': response.meta.get('keyword'),
                'search_url': response.url
            })
    
    def parse_article(self, response):
        """Parse individual article"""
        try:
            # Extract article data
            title = response.css('h1.tit::text').get()
            if not title:
                title = response.css('div.article-head h1::text').get()
            
            # Extract date
            date_str = response.css('p.info-text01 span.txt-time::text').get()
            if not date_str:
                date_str = response.css('div.article-head p.info span.date::text').get()
            
            # Extract content
            content_elements = response.css('div.article p::text').getall()
            if not content_elements:
                content_elements = response.css('div.story-news p::text').getall()
            
            content = ' '.join(content_elements).strip() if content_elements else ''
            
            # Extract author
            author = response.css('p.info-text01 span.txt-author::text').get()
            if not author:
                author = response.css('div.article-head p.info span.author::text').get()
            
            # Parse date
            article_date = None
            if date_str:
                try:
                    # Try different date formats
                    for fmt in ['%Y-%m-%d %H:%M', '%Y.%m.%d %H:%M', '%Y/%m/%d %H:%M']:
                        try:
                            article_date = datetime.strptime(date_str.strip(), fmt).date()
                            break
                        except ValueError:
                            continue
                except:
                    pass
            
            if title and content and article_date:
                yield {
                    'date': article_date.strftime('%Y-%m-%d'),
                    'title': title.strip(),
                    'content': content,
                    'link': response.url,
                    'author': author.strip() if author else '',
                    'source': 'yonhap',
                    'keyword': response.meta.get('keyword', '')
                }
                
        except Exception as e:
            self.logger.error(f"Error parsing article {response.url}: {e}")