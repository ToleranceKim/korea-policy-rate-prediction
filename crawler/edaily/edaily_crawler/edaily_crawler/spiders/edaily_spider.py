import scrapy
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin


class EdailySpider(scrapy.Spider):
    name = "edaily_spider"
    allowed_domains = ["edaily.co.kr"]
    
    def start_requests(self):
        """Generate requests for financial news from Edaily"""
        # Financial keywords for Korean monetary policy
        keywords = [
            "금리", "기준금리", "통화정책", "금융통화위원회", "한국은행",
            "콜금리", "금통위", "기준금리인상", "기준금리인하", "통화정책방향"
        ]
        
        base_url = "https://www.edaily.co.kr/search/news"
        
        for keyword in keywords:
            for page in range(1, 31):  # Limit to 30 pages per keyword
                params = {
                    'keyword': keyword,
                    'newsType': 'title_content',
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
        article_links = response.css('div.newsbox_01 dl dt a::attr(href)').getall()
        
        if not article_links:
            # Try alternative selector
            article_links = response.css('div.news_list li h4 a::attr(href)').getall()
        
        for link in article_links:
            if link:
                if not link.startswith('http'):
                    link = urljoin('https://www.edaily.co.kr', link)
                
                yield response.follow(link, self.parse_article, meta={
                    'keyword': response.meta.get('keyword'),
                    'search_url': response.url
                })
    
    def parse_article(self, response):
        """Parse individual article"""
        try:
            # Extract title
            title = response.css('div.news_titles h1::text').get()
            if not title:
                title = response.css('h1.news_title::text').get()
            
            # Extract date
            date_str = response.css('div.news_tool_01 span.dates::text').get()
            if not date_str:
                date_str = response.css('div.article_tool span.date::text').get()
            
            # Extract content
            content_elements = response.css('div.news_body p::text').getall()
            if not content_elements:
                content_elements = response.css('div.ArticleView p::text').getall()
            
            content = ' '.join([elem.strip() for elem in content_elements if elem.strip()])
            
            # Extract author/reporter
            author = response.css('div.news_tool_01 span.reporters::text').get()
            if not author:
                author = response.css('div.article_tool span.reporter::text').get()
            
            # Parse date
            article_date = None
            if date_str:
                try:
                    # Clean date string
                    date_clean = re.sub(r'[^\d\-\s:]', '', date_str)
                    
                    # Try different date formats
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']:
                        try:
                            article_date = datetime.strptime(date_clean.strip(), fmt).date()
                            break
                        except ValueError:
                            continue
                except:
                    pass
            
            # Filter for relevant financial content
            if title and content and article_date:
                financial_keywords = ['금리', '통화정책', '한국은행', '금융통화위원회', '기준금리', '콜금리']
                
                # Check if article is relevant to monetary policy
                text_check = (title + ' ' + content).lower()
                if any(keyword in text_check for keyword in financial_keywords):
                    yield {
                        'date': article_date.strftime('%Y-%m-%d'),
                        'title': title.strip(),
                        'content': content,
                        'link': response.url,
                        'author': author.strip() if author else '',
                        'source': 'edaily',
                        'keyword': response.meta.get('keyword', '')
                    }
                    
        except Exception as e:
            self.logger.error(f"Error parsing article {response.url}: {e}")