import scrapy
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin


class EdailyFixedSpider(scrapy.Spider):
    name = "edaily_fixed"
    allowed_domains = ["edaily.co.kr"]
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
        'FEED_EXPORT_ENCODING': 'utf-8'
    }
    
    def __init__(self, start_date=None, end_date=None, *args, **kwargs):
        super(EdailyFixedSpider, self).__init__(*args, **kwargs)
        self.start_date = start_date
        self.end_date = end_date
        
        # 날짜 범위가 지정되지 않은 경우 전체 기간 사용
        if not self.start_date or not self.end_date:
            self.start_date = "2015-01-01"
            self.end_date = datetime.now().strftime('%Y-%m-%d')
        
        self.logger.info(f"Edaily crawler initialized with date range: {self.start_date} ~ {self.end_date}")
    
    def start_requests(self):
        """Generate requests for financial news from Edaily focusing on interest rates"""
        # Focus on 금리 keyword for comprehensive interest rate coverage
        keyword = "금리"
        base_url = "https://www.edaily.co.kr/search/news"
        
        # Search with date range parameters for monthly collection
        for page in range(1, 101):  # Search 100 pages to get comprehensive data
            params = {
                'keyword': keyword,
                'newsType': 'title_content',  # Search both title and content
                'period': 'input_period',  # Custom date range
                'startDate': self.start_date,  # Start date for filtering
                'endDate': self.end_date,  # End date for filtering
                'page': page
            }
            
            url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={'keyword': keyword, 'page': page, 'date_range': f"{self.start_date}~{self.end_date}"},
                headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
    
    def parse(self, response):
        """Parse search results and extract article links using correct selectors"""
        self.logger.info(f"Parsing search page {response.meta.get('page')} for keyword '{response.meta.get('keyword')}'")
        
        # Use the correct selector based on actual HTML structure analysis
        article_containers = response.css('div.newsbox_04')
        
        self.logger.info(f"Found {len(article_containers)} article containers")
        
        for container in article_containers:
            # Extract article link
            link = container.css('a::attr(href)').get()
            
            # Extract title for preliminary filtering
            title = container.css('a ul.newsbox_texts li::text').get()
            
            if link and title:
                if not link.startswith('http'):
                    link = urljoin('https://www.edaily.co.kr', link)
                
                # Pre-filter for financial/monetary policy relevance
                financial_keywords = ['금리', '기준금리', '통화정책', '한국은행', '금융통화위원회', '콜금리', '금통위', 'BOK', '이자율']
                title_lower = title.lower()
                
                if any(keyword in title_lower for keyword in financial_keywords):
                    self.logger.info(f"Found relevant article: {title[:50]}...")
                    yield response.follow(link, self.parse_article, meta={
                        'keyword': response.meta.get('keyword'),
                        'search_url': response.url,
                        'search_title': title
                    })
        
        # Check if there are more pages (look for pagination)
        current_page = response.meta.get('page', 1)
        if current_page <= 100 and article_containers:  # Continue if we found articles
            self.logger.info(f"Page {current_page} processed successfully, continuing...")
        else:
            self.logger.info(f"No more articles found on page {current_page}, stopping...")
    
    def parse_article(self, response):
        """Parse individual article with improved selectors"""
        try:
            # Extract title - try multiple selectors
            title = response.css('div.news_titles h1::text').get()
            if not title:
                title = response.css('h1.news_title::text').get()
            if not title:
                title = response.css('div.article_head h1::text').get()
            if not title:
                title = response.meta.get('search_title', '')  # Fallback to search result title
            
            # Extract date - try multiple selectors
            date_str = None
            date_selectors = [
                'div.news_tool_01 span.dates::text',
                'div.article_tool span.date::text', 
                'div.news_info span.date::text',
                'p.article_date::text'
            ]
            
            for selector in date_selectors:
                date_str = response.css(selector).get()
                if date_str:
                    break
            
            # Extract content - get full text from content containers  
            content = None
            content_selectors = [
                'div.news_body',
                'div.ArticleView', 
                'div.article_content'
            ]
            
            for selector in content_selectors:
                content_div = response.css(selector).get()
                if content_div:
                    # Extract text from the entire div, not just p tags
                    from scrapy import Selector
                    content_selector = Selector(text=content_div)
                    content_text = content_selector.css('::text').getall()
                    # Clean and join text, excluding very short fragments
                    content = ' '.join([text.strip() for text in content_text if text.strip() and len(text.strip()) > 5])
                    if len(content) > 100:  # Only use if substantial content found
                        break
            
            # Fallback to p tags if div extraction failed
            if not content or len(content) < 100:
                content_elements = response.css('div.news_body p::text, div.ArticleView p::text, div.article_content p::text').getall()
                if content_elements:
                    content = ' '.join([elem.strip() for elem in content_elements if elem.strip() and len(elem.strip()) > 10])
                else:
                    # Final fallback - get all p tags
                    all_p_text = response.css('p::text').getall()
                    content = ' '.join([text.strip() for text in all_p_text if text.strip() and len(text.strip()) > 10])
            
            # Extract author/reporter
            author = response.css('div.news_tool_01 span.reporters::text').get()
            if not author:
                author = response.css('div.article_tool span.reporter::text').get()
            if not author:
                author = response.css('span.reporter::text').get()
            
            # Parse date
            article_date = None
            if date_str:
                try:
                    # Clean date string - remove Korean characters and extra spaces
                    date_clean = re.sub(r'[가-힣\[\]()]', '', date_str).strip()
                    date_clean = re.sub(r'\s+', ' ', date_clean)
                    
                    # Try different date formats
                    date_formats = [
                        '%Y-%m-%d %H:%M:%S',
                        '%Y-%m-%d %H:%M', 
                        '%Y-%m-%d',
                        '%Y.%m.%d %H:%M:%S',
                        '%Y.%m.%d %H:%M',
                        '%Y.%m.%d',
                        '%Y/%m/%d %H:%M:%S',
                        '%Y/%m/%d %H:%M',
                        '%Y/%m/%d'
                    ]
                    
                    for fmt in date_formats:
                        try:
                            article_date = datetime.strptime(date_clean.strip(), fmt).date()
                            break
                        except ValueError:
                            continue
                            
                    # If still no date, try to extract year-month-day numbers
                    if not article_date:
                        date_match = re.search(r'(\d{4})[-./ ](\d{1,2})[-./ ](\d{1,2})', date_str)
                        if date_match:
                            try:
                                year, month, day = date_match.groups()
                                article_date = datetime(int(year), int(month), int(day)).date()
                            except ValueError:
                                pass
                                
                except Exception as e:
                    self.logger.warning(f"Date parsing error for '{date_str}': {e}")
            
            # Enhanced content filtering for financial relevance
            if title and content:
                financial_keywords = [
                    '금리', '기준금리', '통화정책', '한국은행', '금융통화위원회', 
                    '콜금리', '금통위', 'BOK', '이자율', '통화정책방향',
                    '기준금리인상', '기준금리인하', '기준금리동결', '정책금리',
                    'FOMC', '연준', '중앙은행', '통화완화', '통화긴축'
                ]
                
                # Check relevance in both title and content
                text_check = (title + ' ' + content).lower()
                relevance_score = sum(1 for keyword in financial_keywords if keyword in text_check)
                
                # Only yield if article has financial relevance and minimum content length
                if relevance_score > 0 and len(content) > 100:
                    
                    # Set default date if parsing failed
                    if not article_date:
                        article_date = datetime.now().date()
                        self.logger.warning(f"Using current date as fallback for article: {title[:50]}...")
                    
                    yield {
                        'date': article_date.strftime('%Y-%m-%d'),
                        'title': title.strip(),
                        'content': content,
                        'link': response.url,
                        'author': author.strip() if author else '',
                        'source': 'edaily',
                        'keyword': response.meta.get('keyword', ''),
                        'relevance_score': relevance_score,
                        'content_length': len(content)
                    }
                    
                    self.logger.info(f"Successfully extracted article: {title[:50]}... (Date: {article_date}, Score: {relevance_score})")
                else:
                    self.logger.debug(f"Article filtered out - Score: {relevance_score}, Content length: {len(content)}")
                    
        except Exception as e:
            self.logger.error(f"Error parsing article {response.url}: {e}")
            # Still try to yield basic info if possible
            title = response.meta.get('search_title', 'Error parsing title')
            yield {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'title': title,
                'content': f'Error parsing content: {str(e)}',
                'link': response.url,
                'author': '',
                'source': 'edaily',
                'keyword': response.meta.get('keyword', ''),
                'relevance_score': 0,
                'content_length': 0,
                'error': str(e)
            }