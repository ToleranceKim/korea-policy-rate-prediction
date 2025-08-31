#!/usr/bin/env python3
"""
이데일리 크롤러 - 실제 작동하는 버전
작년 코드 기반으로 복구
"""

import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import json
import time
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EdailyWorkingCrawler:
    """이데일리 실제 작동 크롤러"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        self.contents = []
        self.date_list = []
        self.url_list = []
        
    def crawl_edaily(self, start, end, max_pages=None):
        """
        이데일리 크롤링 함수
        
        Args:
            start: 시작날짜 (YYYYMMDD 형식, 예: 20190101)
            end: 종료날짜 (YYYYMMDD 형식, 예: 20190131)
            max_pages: 최대 페이지 수 (None이면 모든 페이지)
        """
        
        logger.info(f"이데일리 크롤링 시작: {start} ~ {end}")
        
        # URL 템플릿 (작년 코드와 동일)
        base_url = f'https://www.edaily.co.kr/search/news/?source=total&keyword=금리&include=&exclude=&jname=&start={start}&end={end}&sort=latest&date=pick&exact=false&page='
        
        page_number = 1
        empty_page_count = 0
        
        while True:
            # 페이지 제한 확인
            if max_pages and page_number > max_pages:
                logger.info(f"최대 페이지({max_pages}) 도달")
                break
                
            current_url = base_url + str(page_number)
            
            try:
                response = requests.get(current_url, headers=self.headers, timeout=10)
                
                if response.status_code != 200:
                    logger.error(f"HTTP {response.status_code}")
                    break
                    
                soup = bs(response.text, 'html.parser')
                
                # 뉴스 기사 추출
                news_items = soup.select('.newsbox_04')
                
                if not news_items:
                    empty_page_count += 1
                    logger.info(f"페이지 {page_number}: 결과 없음")
                    if empty_page_count >= 3:
                        logger.info("3페이지 연속 결과 없음, 종료")
                        break
                else:
                    empty_page_count = 0
                    logger.info(f"페이지 {page_number}: {len(news_items)}개 기사 발견")
                
                for item in news_items:
                    # 제목과 내용 추출
                    text_elem = item.select_one('.newsbox_texts')
                    if text_elem:
                        content = text_elem.text.strip()
                        self.contents.append(content)
                        
                        # URL 추출
                        link_tag = item.find('a', href=True)
                        if link_tag:
                            url = 'https://www.edaily.co.kr' + link_tag['href']
                            self.url_list.append(url)
                        else:
                            self.url_list.append(None)
                    
                    # 날짜 추출
                    date_elem = item.select_one('.author_category')
                    if date_elem:
                        date_text = date_elem.text.split()[0]
                        self.date_list.append(date_text)
                
                page_number += 1
                time.sleep(0.5)  # 서버 부하 방지
                
            except Exception as e:
                logger.error(f"페이지 {page_number} 오류: {e}")
                break
        
        logger.info(f"크롤링 완료: 총 {len(self.contents)}개 기사 수집")
        return self.contents, self.date_list, self.url_list
    
    def save_to_json(self, filename='edaily_output.json'):
        """JSON 형식으로 저장"""
        
        articles = []
        for i in range(len(self.contents)):
            # 제목과 내용 분리 (첫 줄이 제목)
            lines = self.contents[i].split('\n')
            title = lines[0] if lines else ""
            content = '\n'.join(lines[1:]) if len(lines) > 1 else ""
            
            article = {
                'date': self.date_list[i] if i < len(self.date_list) else None,
                'title': title,
                'content': content,
                'url': self.url_list[i] if i < len(self.url_list) else None,
                'source': 'edaily'
            }
            articles.append(article)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        logger.info(f"저장 완료: {filename}")
        return articles
    
    def save_to_csv(self, filename='edaily_output.csv'):
        """CSV 형식으로 저장 (작년 코드와 동일)"""
        
        data = {
            "DATE": self.date_list,
            "CONTENTS": self.contents,
            "URL": self.url_list
        }
        df = pd.DataFrame(data)
        
        # 날짜순 정렬
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
        df = df.sort_values(by='DATE')
        
        # 번호 추가
        df.insert(0, 'No.', range(1, len(df) + 1))
        
        # 제목 분리
        df['TITLE'] = df['CONTENTS'].str.split('\n').str[0]
        df['CONTENTS'] = df['CONTENTS'].str.split('\n').str[1:]
        df['CONTENTS'] = df['CONTENTS'].apply(lambda x: '\n'.join(x) if isinstance(x, list) else x)
        
        # 중복 제거
        df = df.drop_duplicates(subset=['TITLE', 'DATE'], keep='first')
        
        # CSV 저장
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        logger.info(f"CSV 저장 완료: {filename} ({len(df)}개 기사)")
        return df


def test_edaily():
    """이데일리 크롤러 테스트"""
    
    crawler = EdailyWorkingCrawler()
    
    # 2019년 1월 테스트 (최대 5페이지)
    print("\n=== 이데일리 2019년 1월 테스트 ===")
    crawler.crawl_edaily(20190101, 20190131, max_pages=5)
    
    # JSON으로 저장
    articles = crawler.save_to_json('/tmp/edaily_2019_01_test.json')
    
    print(f"\n수집 결과:")
    print(f"- 총 기사 수: {len(articles)}")
    
    if articles:
        print(f"\n첫 3개 기사:")
        for i, article in enumerate(articles[:3], 1):
            print(f"{i}. [{article['date']}] {article['title'][:50]}")
    
    # CSV로도 저장
    df = crawler.save_to_csv('/tmp/edaily_2019_01_test.csv')
    
    return articles


def crawl_full_period(start_date, end_date):
    """전체 기간 크롤링 (작년 코드처럼)"""
    
    periods = [
        (20140811, 20150131),
        (20150201, 20150731),
        (20150801, 20160131),
        (20160201, 20160731),
        (20160801, 20170131),
        (20170201, 20170731),
        (20170801, 20180131),
        (20180201, 20180731),
        (20180801, 20190131),
        (20190201, 20190731),
        (20190801, 20200131),
        (20200201, 20200731),
        (20200801, 20210131),
        (20210201, 20210731),
        (20210801, 20220131),
        (20220201, 20220731),
        (20220801, 20230131),
        (20230201, 20230731),
        (20230801, 20240131),
        (20240201, 20240831)
    ]
    
    all_articles = []
    
    for start, end in periods:
        if start >= int(start_date.replace('-', '')) and end <= int(end_date.replace('-', '')):
            logger.info(f"\n기간: {start} ~ {end}")
            
            crawler = EdailyWorkingCrawler()
            crawler.crawl_edaily(start, end)
            articles = crawler.save_to_json(f'/tmp/edaily_{start}_{end}.json')
            all_articles.extend(articles)
            
            time.sleep(2)  # 서버 부하 방지
    
    # 전체 데이터 저장
    with open('/tmp/edaily_all.json', 'w', encoding='utf-8') as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n전체 수집 완료: {len(all_articles)}개")
    return all_articles


if __name__ == "__main__":
    test_edaily()