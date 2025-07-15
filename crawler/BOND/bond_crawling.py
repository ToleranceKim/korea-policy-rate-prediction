# 3 muti threading (PDF to CSV, date+link)

from bs4 import BeautifulSoup
import requests
import time
import re
from requests import get
from urllib import request
from PyPDF2 import PdfReader
import os
import csv
from pykospacing import Spacing
import shutil
from tika import parser
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 1
today = "2024-08-11"
target_day = "2014-08-11"

url = f"https://finance.naver.com/research/debenture_list.naver?keyword=&brokerCode=&searchType=writeDate&writeFromDate={target_day}&writeToDate={today}&x=0&y=0&page=1"
temp_url = "https://finance.naver.com/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36', 
    'Referer': 'https://www.naver.com/'
}

# 2
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

last_page = soup.select_one('td.pgRR>a').attrs['href']
temp = f"/research/debenture_list.naver?keyword=&brokerCode=&searchType=writeDate&writeFromDate={target_day}&writeToDate={today}&x=0&y=0&page="
pages = int(last_page.replace(temp,''))

# Function to process individual reports
def process_report(report_link):
    normal_page = "https://finance.naver.com/research/"
    report_page = normal_page + report_link.attrs['href']

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36', 
        'Referer': 'https://www.naver.com/'
    }
    response = requests.get(report_page, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    try:
        report_info = soup.select_one('p.source').text.strip().replace("\n", '').replace("\t", '')
        report_info = report_info.split("|")
        cop_name = report_info[0]
        published_date = report_info[1]

        # 리포트 제목 추출
        report_title = soup.select_one('th.view_sbj').text.strip().replace("\n", '').replace("\t", '')
        title = report_title.split(cop_name)[0].strip()
        title = title.replace('/', '_')  # Replace "/" with "_" to avoid file path issues
        print(f"리서치 제목 : {title}")

        # 리포트 전체 내용 추출(PDF 포함)
        content = soup.select_one("td.view_cnt").text.strip().replace('\n', '')

        # PDF 추출
        pdf_link = soup.select_one("a.con_link").attrs['href'] if soup.select("a.con_link") else None
        pdf_name = soup.select("a.con_link")[1].text.replace('/', '_') if len(soup.select("a.con_link")) > 1 else None

        if pdf_name:
            print("PDF 파일이 존재합니다")
            content = content.split(pdf_name)[0]  # 내용과 PDF 분리

            # PDF 저장
            with open(pdf_name, "wb") as file:   # open in binary mode
                response = get(pdf_link)
                file.write(response.content)
                time.sleep(1)

            # PDF 텍스트 추출
            parsed = parser.from_file(pdf_name)
            text = parsed['content']

            if text:
                new_str = re.sub("\n", "", text)
                new_str = re.sub(" ", "", new_str)

                spacing = Spacing()
                kospacing_result = spacing(new_str)

                directory = f'./dataset_2'
                os.makedirs(directory, exist_ok=True)  # 디렉토리가 없으면 생성

                # CSV 파일에 데이터 저장
                csv_file_path = f'{directory}/{published_date}_{title}_{cop_name}.csv'
                with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    csvwriter = csv.writer(csvfile)
                    csvwriter.writerow(['Date', 'Title', 'Content', 'Link'])  # CSV 헤더
                    csvwriter.writerow([published_date, title, kospacing_result, pdf_link])  # CSV 데이터

                print(f"Saved CSV: {csv_file_path}")

                # PDF 파일 삭제
                os.remove(pdf_name)
            else:
                print(f"PDF 파일을 읽을 수 없습니다: {pdf_name}")
        else:
            print(f"PDF 파일이 없습니다, 이 경우엔 수집하지 않습니다: {title}")

    except Exception as e:
        print(f"Failed to process report: {report_page}, error: {e}")

# Function to process each page of reports
def process_page(page):
    page_url = f"https://finance.naver.com/research/debenture_list.naver?keyword=&brokerCode=&searchType=writeDate&writeFromDate={target_day}&writeToDate={today}&x=0&y=0&page={page}"
    response = requests.get(page_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    reports = soup.select('table.type_1 tr')

    with ThreadPoolExecutor(max_workers=10) as report_executor:
        futures = [report_executor.submit(process_report, report.select_one("a")) for report in reports if report.select_one("a")]
        for future in as_completed(futures):
            future.result()

# 3
with ThreadPoolExecutor(max_workers=10) as page_executor:
    futures = [page_executor.submit(process_page, page) for page in range(1, pages + 1)]
    for future in as_completed(futures):
        future.result()
