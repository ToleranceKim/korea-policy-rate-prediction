# Scrapy settings for edaily_crawler project

BOT_NAME = 'edaily_crawler'

SPIDER_MODULES = ['edaily_crawler.spiders']
NEWSPIDER_MODULE = 'edaily_crawler.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure delays for requests
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = 0.5

# Configure user agent
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'

# Configure concurrent requests
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# Configure AutoThrottle
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# Configure feed exports
FEEDS = {
    'edaily_output.json': {
        'format': 'json',
        'encoding': 'utf8',
        'ensure_ascii': False,
    },
}