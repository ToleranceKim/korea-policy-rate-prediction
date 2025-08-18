import scrapy
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, quote


class YhFixedSpider(scrapy.Spider):
    name = "yh_fixed"
    allowed_domains = ["yna.co.kr"]
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': 1.0,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 15,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'FEED_EXPORT_ENCODING': 'utf-8',
        'COOKIES_ENABLED': True,
        'ROBOTSTXT_OBEY': False,  # Temporarily disable to test
    }
    
    def __init__(self, start_date=None, end_date=None, *args, **kwargs):
        super(YhFixedSpider, self).__init__(*args, **kwargs)
        self.start_date_param = start_date
        self.end_date_param = end_date
        
        self.logger.info(f"Yonhap crawler initialized with date range: {start_date} ~ {end_date}")
    
    def start_requests(self):
        """Generate requests for historical data using year-based approach"""
        
        # Use year-based approach for data collection
        # Only /economy/finance section supports year parameter based on research
        base_url = "https://www.yna.co.kr"
        section = '/economy/finance'  # Only this section allows historical access
        
        # Determine year range from date parameters
        if self.start_date_param and self.end_date_param:
            start_year = datetime.strptime(self.start_date_param, '%Y-%m-%d').year
            end_year = datetime.strptime(self.end_date_param, '%Y-%m-%d').year
        else:
            start_year = 2015
            end_year = 2025
        
        self.logger.info(f"🎯 Starting 10-year historical crawl: {start_year}-{end_year}")
        
        # Generate requests for each year
        for year in range(start_year, end_year + 1):
            url = f"{base_url}{section}?year={year}"
            yield scrapy.Request(
                url=url,
                callback=self.parse_year_section,
                meta={'section': section, 'year': year},
                headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                }
            )
        
        # Also try alternative search approach
        keyword = "금리"
        # Try different search URL formats
        search_urls = [
            f"https://www.yna.co.kr/search?query={quote(keyword)}&sort=date",
            f"https://www.yna.co.kr/search?query={quote(keyword)}&sort=1",
            f"https://www.yna.co.kr/search?q={quote(keyword)}",
        ]
        
        for search_url in search_urls:
            yield scrapy.Request(
                url=search_url,
                callback=self.parse_search,
                meta={'keyword': keyword, 'search_type': 'direct'},
                headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Referer': 'https://www.yna.co.kr/',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate', 
                    'Sec-Fetch-Site': 'same-origin',
                },
                dont_filter=True
            )
    
    def parse_year_section(self, response):
        """Parse year-based finance section to find articles with '금리' keyword"""
        year = response.meta.get('year')
        section = response.meta.get('section')
        
        self.logger.info(f"📅 Parsing {year} finance section: {section}")
        
        # Extract all article links from the year page
        article_selectors = [
            'a[href*="/view/"]',
            'a[href*="/AKR"]',
            '.news-con a',
            '.list-type01 a',
            '.news-item a'
        ]
        
        article_links = []
        for selector in article_selectors:
            links = response.css(selector + '::attr(href)').getall()
            article_links.extend(links)
        
        self.logger.info(f"Found {len(article_links)} potential article links for {year}")
        
        # Process each article link
        for link in article_links:
            if link and '/view/' in link:
                if not link.startswith('http'):
                    article_url = urljoin('https://www.yna.co.kr', link)
                else:
                    article_url = link
                
                yield response.follow(article_url, self.parse_article, meta={
                    'year': year,
                    'section': section,
                    'source_url': response.url
                })
        
        # Check for pagination or "more articles" links
        next_page_selectors = [
            'a[href*="page="]',
            '.paging a',
            '.pagination a',
            'a:contains("다음")',
            'a:contains("더보기")'
        ]
        
        for selector in next_page_selectors:
            next_links = response.css(selector + '::attr(href)').getall()
            for next_link in next_links:
                if next_link and 'page=' in next_link:
                    next_url = urljoin(response.url, next_link)
                    yield response.follow(next_url, self.parse_year_section, meta={
                        'year': year,
                        'section': section
                    })
                    break  # Follow only one pagination link per page
    
    def parse_section(self, response):
        """Parse financial news sections to find articles"""
        self.logger.info(f"Parsing section: {response.meta.get('section')}")
        
        # Look for article links in the section page
        article_links = []
        
        # Try various selectors for article links
        selectors_to_try = [
            'div.list-type038 li dt a::attr(href)',
            'div.list-type01 li a::attr(href)', 
            'ul.list li a::attr(href)',
            'div.news-list li a::attr(href)',
            'a[href*="/view/"]::attr(href)',
            'a[href*="/news/"]::attr(href)'
        ]
        
        for selector in selectors_to_try:
            links = response.css(selector).getall()
            if links:
                article_links.extend(links)
                self.logger.info(f"Found {len(links)} links with selector: {selector}")
        
        # Process found links
        for link in article_links[:20]:  # Limit to first 20 articles per section
            if link:
                if not link.startswith('http'):
                    link = urljoin('https://www.yna.co.kr', link)
                
                yield response.follow(link, self.parse_article, meta={
                    'source_section': response.meta.get('section'),
                    'keyword': '금리관련'
                })
    
    def parse_search(self, response):
        """Parse search results if search works"""
        self.logger.info(f"Parsing search results for: {response.meta.get('keyword')}")
        
        if response.status == 200:
            # Look for article links in search results
            selectors_to_try = [
                'div.list-type038 li dt a::attr(href)',
                'div.search-result li a::attr(href)',
                'ul.news-list li a::attr(href)',
                'a[href*="/view/"]::attr(href)'
            ]
            
            found_articles = False
            for selector in selectors_to_try:
                article_links = response.css(selector).getall()
                if article_links:
                    found_articles = True
                    self.logger.info(f"Found {len(article_links)} articles with selector: {selector}")
                    
                    for link in article_links[:30]:  # Process first 30 results
                        if link:
                            if not link.startswith('http'):
                                link = urljoin('https://www.yna.co.kr', link)
                            
                            yield response.follow(link, self.parse_article, meta={
                                'keyword': response.meta.get('keyword'),
                                'search_url': response.url
                            })
                    break
            
            if not found_articles:
                self.logger.warning(f"No articles found in search results. Status: {response.status}")
        else:
            self.logger.error(f"Search failed with status: {response.status}")
    
    def parse_article(self, response):
        """Parse individual article with comprehensive selectors"""
        try:
            # Extract title - try multiple selectors
            title_selectors = [
                'h1.tit::text',
                'div.article-head h1::text',
                'h1.news-tit::text',
                'div.view-head h1::text',
                'h1::text'
            ]
            
            title = None
            for selector in title_selectors:
                title = response.css(selector).get()
                if title:
                    break
            
            # Extract date
            date_selectors = [
                'p.info-text01 span.txt-time::text',
                'div.article-head p.info span.date::text',
                'div.view-head p.info span.date::text',
                'span.date::text',
                'p.date::text'
            ]
            
            date_str = None
            for selector in date_selectors:
                date_str = response.css(selector).get()
                if date_str:
                    break
            
            # Extract content
            content_selectors = [
                'div.article p::text',
                'div.story-news p::text',
                'div.view-cont p::text',
                'div.news-content p::text'
            ]
            
            content_elements = []
            for selector in content_selectors:
                content_elements = response.css(selector).getall()
                if content_elements:
                    break
            
            content = ' '.join([elem.strip() for elem in content_elements if elem.strip()]).strip()
            
            # Extract author
            author_selectors = [
                'p.info-text01 span.txt-author::text',
                'div.article-head p.info span.author::text',
                'span.author::text',
                'p.author::text'
            ]
            
            author = None
            for selector in author_selectors:
                author = response.css(selector).get()
                if author:
                    break
            
            # Parse date
            article_date = None
            if date_str:
                try:
                    # Clean date string
                    date_clean = re.sub(r'[^\d\-\.\s:]', '', date_str).strip()
                    
                    # Try different date formats
                    date_formats = [
                        '%Y-%m-%d %H:%M',
                        '%Y.%m.%d %H:%M', 
                        '%Y/%m/%d %H:%M',
                        '%Y-%m-%d',
                        '%Y.%m.%d',
                        '%Y/%m/%d'
                    ]
                    
                    for fmt in date_formats:
                        try:
                            article_date = datetime.strptime(date_clean.strip(), fmt).date()
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    self.logger.warning(f"Date parsing failed for '{date_str}': {e}")
            
            # Unified keyword filtering: Focus on "금리" keyword for consistency across all crawlers
            if title and content:
                # Simple and consistent filtering: articles containing "금리" keyword
                text_check = (title + ' ' + content).lower()
                has_interest_rate_keyword = '금리' in text_check
                
                # Calculate simple relevance score based on "금리" occurrences
                relevance_score = text_check.count('금리')
                
                # Only yield articles containing "금리" keyword with substantial content
                if has_interest_rate_keyword and len(content) > 100:
                    
                    if not article_date:
                        article_date = datetime.now().date()
                    
                    yield {
                        'date': article_date.strftime('%Y-%m-%d'),
                        'title': title.strip(),
                        'content': content,
                        'link': response.url,
                        'author': author.strip() if author else '',
                        'source': 'yonhap',
                        'keyword': response.meta.get('keyword', ''),
                        'source_section': response.meta.get('source_section', ''),
                        'relevance_score': relevance_score,
                        'content_length': len(content)
                    }
                    
                    self.logger.info(f"Successfully extracted Yonhap article: {title[:50]}...")
                
        except Exception as e:
            self.logger.error(f"Error parsing Yonhap article {response.url}: {e}")
            
    def start_requests_fallback(self):
        """Alternative approach if main search fails"""
        # Try RSS feeds if available
        rss_feeds = [
            'https://www.yna.co.kr/rss/economy.xml',
            'https://www.yna.co.kr/rss/finance.xml',
        ]
        
        for feed_url in rss_feeds:
            yield scrapy.Request(
                url=feed_url,
                callback=self.parse_rss,
                meta={'feed_type': 'rss'}
            )