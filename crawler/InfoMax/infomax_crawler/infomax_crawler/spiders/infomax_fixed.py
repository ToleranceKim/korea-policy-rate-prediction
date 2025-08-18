import scrapy
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, quote

class InfomaxFixedSpider(scrapy.Spider):
    name = "infomax_fixed"
    allowed_domains = ["einfomax.co.kr"]
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': 1.0,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
        'FEED_EXPORT_ENCODING': 'utf-8',
        'COOKIES_ENABLED': True,
        'ROBOTSTXT_OBEY': False
    }
    
    def __init__(self, start_date=None, end_date=None, *args, **kwargs):
        super(InfomaxFixedSpider, self).__init__(*args, **kwargs)
        self.start_date_param = start_date
        self.end_date_param = end_date
        
        self.logger.info(f"InfoMax crawler initialized with date range: {start_date} ~ {end_date}")
    
    def start_requests(self):
        """Generate requests for InfoMax financial news focusing on interest rates"""
        keyword = "금리"
        
        # Use provided date range or default to 10-year range
        if self.start_date_param and self.end_date_param:
            start_date = datetime.strptime(self.start_date_param, '%Y-%m-%d')
            end_date = datetime.strptime(self.end_date_param, '%Y-%m-%d')
        else:
            # Set 10-year date range for comprehensive historical data collection
            end_date = datetime.now()
            start_date = datetime(2015, 1, 1)  # 10-year historical data: 2015-2025
        
        sc_sdate = start_date.strftime('%Y-%m-%d')
        sc_edate = end_date.strftime('%Y-%m-%d')
        
        # Start with first page to determine total pages
        for page in range(1, 51):  # Limit to first 50 pages for efficiency
            url = f"https://news.einfomax.co.kr/news/articleList.html?page={page}&total=6417&sc_section_code=&sc_sub_section_code=&sc_serial_code=&sc_area=A&sc_level=&sc_article_type=&sc_view_level=&sc_sdate={sc_sdate}&sc_edate={sc_edate}&sc_serial_number=&sc_word={quote(keyword)}&box_idxno=&sc_multi_code=&sc_is_image=&sc_is_movie=&sc_user_name=&sc_order_by=E&view_type=sm"
            
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={'keyword': keyword, 'page': page},
                headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Referer': 'https://news.einfomax.co.kr/'
                }
            )
    
    def parse(self, response):
        """Parse search results page and extract article links"""
        self.logger.info(f"Parsing InfoMax page {response.meta.get('page')} for keyword '{response.meta.get('keyword')}'")
        
        # Extract article links using the selector from the notebook
        article_links = response.css('ul.type2 > li > h4.titles > a::attr(href)').getall()
        
        self.logger.info(f"Found {len(article_links)} article links")
        
        if not article_links:
            self.logger.warning(f"No articles found on page {response.meta.get('page')}")
            return
        
        # Process each article link
        for link in article_links:
            if link:
                if not link.startswith('http'):
                    article_url = urljoin('https://news.einfomax.co.kr', link)
                else:
                    article_url = link
                
                yield response.follow(article_url, self.parse_article, meta={
                    'keyword': response.meta.get('keyword'),
                    'source_page': response.url
                })
    
    def parse_article(self, response):
        """Parse individual InfoMax article"""
        try:
            # Extract title using the selector from the notebook
            title = response.css('h3.heading::text').get()
            if not title:
                title = response.css('h1::text, h2::text, h3::text').get()
            
            if not title:
                self.logger.warning(f"No title found for article: {response.url}")
                return
            
            title = title.strip()
            
            # Extract date from infomation list
            date_str = None
            info_items = response.css('ul.infomation > li::text').getall()
            for item in info_items:
                if '입력' in item:
                    date_str = item.split("입력")[-1].strip()
                    break
            
            # Extract content using improved selectors based on analysis
            content = None
            
            # Try primary content selector
            content_div = response.css('.article-body::text').getall()
            if content_div:
                content = ' '.join([text.strip() for text in content_div if text.strip()])
            
            # Fallback to original selector
            if not content or len(content) < 50:
                content_div = response.css('#article-view-content-div::text').getall()
                if content_div:
                    content = ' '.join([text.strip() for text in content_div if text.strip()])
            
            # Additional fallback selectors
            if not content or len(content) < 50:
                content_elements = response.css('.article-veiw-body p::text, .article-body p::text').getall()
                if content_elements:
                    content = ' '.join([text.strip() for text in content_elements if text.strip()])
            
            # Final fallback
            if not content or len(content) < 50:
                content_elements = response.css('div[class*="content"] p::text, div[class*="article"] p::text').getall()
                content = ' '.join([text.strip() for text in content_elements if text.strip()])
            
            # Clean up content
            if content:
                content = re.sub(r'\n|\r|\t', ' ', content)
                content = re.sub(r'\s+', ' ', content).strip()
            
            # Extract author/reporter if available
            author = None
            for item in info_items:
                if '기자' in item or '특파원' in item:
                    author = item.strip()
                    break
            
            # Parse date
            article_date = None
            if date_str:
                try:
                    # Clean date string and try various formats
                    date_clean = re.sub(r'[^0-9\-\.\s:]', '', date_str).strip()
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
            
            # Unified keyword filtering: Focus on "금리" keyword for consistency
            if title and content:
                # Simple and consistent filtering: articles containing "금리" keyword
                text_check = (title + ' ' + content).lower()
                has_interest_rate_keyword = '금리' in text_check
                
                # Calculate simple relevance score based on "금리" occurrences
                relevance_score = text_check.count('금리')
                
                # Only yield if article contains "금리" keyword and has minimum content length
                if has_interest_rate_keyword and len(content) > 100:
                    
                    # Set default date if parsing failed
                    if not article_date:
                        article_date = datetime.now().date()
                        self.logger.warning(f"Using current date as fallback for article: {title[:50]}...")
                    
                    yield {
                        'date': article_date.strftime('%Y-%m-%d'),
                        'title': title,
                        'content': content,
                        'link': response.url,
                        'author': author if author else '',
                        'source': 'infomax',
                        'keyword': response.meta.get('keyword', ''),
                        'relevance_score': relevance_score,
                        'content_length': len(content)
                    }
                    
                    self.logger.info(f"Successfully extracted InfoMax article: {title[:50]}... (Date: {article_date}, Score: {relevance_score})")
                else:
                    self.logger.debug(f"Article filtered out - Score: {relevance_score}, Content length: {len(content)}")
                    
        except Exception as e:
            self.logger.error(f"Error parsing InfoMax article {response.url}: {e}")
            # Still try to yield basic info if possible
            title = response.meta.get('title', 'Error parsing title')
            yield {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'title': title,
                'content': f'Error parsing content: {str(e)}',
                'link': response.url,
                'author': '',
                'source': 'infomax',
                'keyword': response.meta.get('keyword', ''),
                'relevance_score': 0,
                'content_length': 0,
                'error': str(e)
            }