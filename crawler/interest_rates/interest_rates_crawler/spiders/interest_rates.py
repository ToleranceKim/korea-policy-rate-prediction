import scrapy
import re
import json


class InterestRatesSpider(scrapy.Spider):
    name = "interest_rates"
    allowed_domains = ["www.bok.or.kr"]

    def start_requests(self):
        base_url = 'https://www.bok.or.kr/portal/singl/baseRate/list.do'
        params = {
            'dataSeCd': '01',
            'menuNo': '200643'
        }
        url = f"{base_url}?{'&'.join([f'{key}={value}' for key, value in params.items()])}"
        yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        # Extract JavaScript data array instead of HTML table
        script_content = response.text
        
        # Find chartObj2_s array data
        pattern = r'var\s+chartObj2_s\s*=\s*(\[[\s\S]*?\]);'
        match = re.search(pattern, script_content)
        
        if match:
            try:
                # Parse the JavaScript array manually using regex patterns
                js_array_str = match.group(1)
                
                # Extract individual data entries using regex
                entry_pattern = r'\["(\d{4}/\d{2}/\d{2}[^"]*)",\s*([0-9.]+)\]'
                entries = re.findall(entry_pattern, js_array_str)
                
                for date_str, rate_str in entries:
                    # Clean up date string (remove trailing spaces)
                    clean_date = date_str.strip()
                    # Convert date format from YYYY/MM/DD to YYYY-MM-DD
                    formatted_date = clean_date.replace('/', '-')
                    
                    # Convert rate to float
                    rate = float(rate_str)
                    
                    yield {
                        '날짜': formatted_date,
                        '기준금리': rate,
                        '원본날짜': clean_date
                    }
                        
                self.logger.info(f"Successfully extracted {len(entries)} interest rate records")
                        
            except (ValueError, AttributeError) as e:
                self.logger.error(f"Error parsing JavaScript data: {e}")
                
        else:
            self.logger.error("Could not find chartObj2_s data array in the page")
