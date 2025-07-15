# Crawler

## 환경설정
<aside>
<b>수집할 기간</b>
<br/>
2014.08.11 ~ 2024.08.11 (10년치)
</aside>
<br/>
<aside>
<b>사용 언어</b>
<br/>
Python 3.8
</aside>

<br/>
<br/>

## 크롤링

### 1. MPB
- 200건
- 날짜, 제목, 내용, 토의내용, 심의결과, 링크만 사용

<br/>

- PDF 파일 다운
```python
base_url = 'https://www.bok.or.kr'
pdf_links = response.css('a.file::attr(href)').getall()
title = response.meta.get('title')
```
<br/>

- 제목에서 날짜 추출
```python
text = parsed["content"]
date_matches = re.findall(r'(\d{4}\.\d{1,2}\.\d{1,2})', response.meta['title'])
date = date_matches[0] if date_matches else None
title = response.meta['title']
```
<br/>

- 추출한 PDF에서 두 번째 섹션(토의내용)과 세 번째 섹션(심의결과)만 사용
```python
# section2 (위원 토의내용) 추출
discussion_pattern = r"위원 토의내용(.*?)심의결과"
discussion_content = re.search(discussion_pattern, text, re.DOTALL)
discussion_text = discussion_content.group(1).strip().replace('\n', '') if discussion_content else None

# section3 (심의결과) 추출
decision_pattern = r"심의결과(.*)"
decision_content = re.search(decision_pattern, text, re.DOTALL)
decision_text = decision_content.group(1).strip().replace('\n', '') if decision_content else None
```
<br/>

- Scrayp 사용

<br/>
<br/>


### 2. 뉴스기사
- 날짜, 제목, 내용, 링크만 사용
- ‘금리’라는 단어가 포함된 뉴스 기사 수집
#### 인포맥스
- 110,000 건

<br/>

- 크롤링할 날짜 선정
```python
sc_sdate = '2015-01-01'  # Start date (YYYY-MM-DD)
sc_edate = '2015-12-31'  # End date (YYYY-MM-DD)
```
<br/>

- 제목 추출
```python
title = crawling_soup.select_one('h3.heading').text
new_title = title.replace("/", "_")  # 타이틀 전처리 결과
```
<br/>

- 날짜 추출
```python
date_li = crawling_soup.select('ul.infomation>li')[1].text
date = date_li.split("입력")[-1].replace('.', '_').replace(':', '_')
```
<br/>

- 내용 추출
```python
info = crawling_soup.select_one('#article-view-content-div').text.replace('\n', '').replace('\r', '').replace('\t', '')
```
<br/>

- 위 과정을 "crawl_page"이름의 함수로 함수화하여 멀티 쓰레딩으로 진행
```python
with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(crawl_page, range(1, pages + 1))
```
<br/>


#### 엽합뉴스
- 63,000 건
- 페이지가 30개씩 나오기 때문에 1개월 단위로 Request를 수행하여 크롤링

<br/>

- 날짜 범위를 1개월 단위로 나누는 함수
```python
def get_monthly_date_ranges(start_date, end_date):
    date_ranges = []
    current_start = start_date
    while current_start < end_date:
        current_end = min(current_start + relativedelta(months=1) - timedelta(days=1), end_date)
        date_ranges.append((current_start, current_end))
        current_start = current_end + timedelta(days=1)
    return date_ranges
```
<br/>

- 날짜 범위를 1개월 단위로 나누는 함수
```python
def get_monthly_date_ranges(start_date, end_date):
    date_ranges = []
    current_start = start_date
    while current_start < end_date:
        current_end = min(current_start + relativedelta(months=1) - timedelta(days=1), end_date)
        date_ranges.append((current_start, current_end))
        current_start = current_end + timedelta(days=1)
    return date_ranges
```
<br/>

- HTTP GET 요청을 재시도하는 함수
```python
def fetch_url_with_retries(url, headers, retries=10, timeout=10):
    for i in range(retries):
        try:
            # print(f"{datetime.now()} - Attempt {i+1} to fetch URL: {url}")
            res = requests.get(url, headers=headers, timeout=timeout)
            if res.status_code == 200:
                return res
            else:
                print(f"Unexpected status code {res.status_code} for URL: {url}")
        except requests.exceptions.RequestException as e:
            print(f"{datetime.now()} - Request failed ({i+1}/{retries}): {e}")
            sleep(2)
    print(f"{datetime.now()} - Failed to retrieve JSON data from {url}")
    return None
```
<br/>

- 파일명에 사용할 수 없는 문자 제거 함수
```python
def clean_filename(filename):
    filename = re.sub(r'[\/:*?"<>|.]', '_', filename)
    filename = re.sub(r'_+', '_', filename)
    return filename.strip('_')
```
<br/>

- 제목, 날짜, 내용 추출
```python
news_title = crawling_soup.select_one('h1.tit').text.strip()

news_date = crawling_soup.select_one('.txt-copyright > span.date').text.strip()[:10].replace("/", ".")

# 모든 p 태그를 찾아 리스트로 저장
p_tags = crawling_soup.find("article", class_="story-news").find_all('p')
# 뒤에서 두 번째까지 제거한 후, 각 p 태그의 텍스트를 추출하여 하나의 문자열로 결합
if len(p_tags) > 2:
    p_tags = p_tags[:-1]
contents = " ".join([p.get_text(strip=True) for p in p_tags])
```
<br/>

- 메인함수 안에서 멀티 쓰레딩 수행
```python
with ThreadPoolExecutor(max_workers=10) as page_executor:
        for date_range in date_ranges:
            from_date = date_range[0].strftime('%Y%m%d')
            to_date = date_range[1].strftime('%Y%m%d')
            futures = [page_executor.submit(process_page, page_no, from_date, to_date, headers, directory) for page_no in range(1, 51)]
            for future in as_completed(futures):
                try:
                    future.result()  # Raise exceptions if any occurred
                except Exception as e:
                    print(f"Error processing page: {e}")
```




#### 이데일리
- 91,765 건
- 한 번에 크롤링이 불가하여 6개월 단위로 분리해서 크롤링을 수행

<br/>

- 제목과 내용 추출
```python
# 뉴스기사 제목, 내용 크롤링
for news_item in soup.select('.newsbox_04 .newsbox_texts'):
    # 뉴스 텍스트 크롤링
    contents.append(news_item.text.strip())
    
    # 기사 URL 크롤링
    link_tag = news_item.find_previous('a')
    if link_tag:
        url = 'https://www.edaily.co.kr' + link_tag['href']
        url_list.append(url)
    else:
        url_list.append(None)
```
<br/>

- 날짜 추출
```python
# 기사 날짜 크롤링
for i in soup.select('.author_category'):
    date_list.append(i.text.split()[0])
```
<br/>

- 중복 기사 조회 후 제거
```python
df[df.duplicated(keep=False)]
df.drop_duplicates(keep='first')
```

<br/>
<br/>

### 3. 채권 분석 보고서
- 페이지에서 PDF를 추출하여 보고서 내용을 크롤링 후 CSV로 변환
- 약 5,909 건

<br/>

- 날짜 선정
```python
today = "2024-08-11"
target_day = "2014-08-11"
```
<br/>

- 리포트 제목 추출 및 포맷 변경
```python
 report_title = soup.select_one('th.view_sbj').text.strip().replace("\n", '').replace("\t", '')
        title = report_title.split(cop_name)[0].strip()
        title = title.replace('/', '_')
        print(f"리서치 제목 : {title}")
```
<br/>

- 리포트 제목 추출 및 포맷 변경
```python

```
<br/>

- PDF 링크를 추출하여 다운로드
```python
# 리포트 전체 내용 추출(PDF 포함)
content = soup.select_one("td.view_cnt").text.strip().replace('\n', '')
# PDF 링크 추출
pdf_link = soup.select_one("a.con_link").attrs['href'] if soup.select("a.con_link") else None
# PDF 제목 추출
pdf_name = soup.select("a.con_link")[1].text.replace('/', '_') if len(soup.select("a.con_link")) > 1 else None
# 내용과 PDF 분리
content = content.split(pdf_name)[0]  

# PDF 저장
with open(pdf_name, "wb") as file: 
    response = get(pdf_link)
    file.write(response.content)
    time.sleep(1)
```
<br/>

- PDF 내용 추출, Kospacing으로 띄워쓰기를 인식하여 추출
```python
parsed = parser.from_file(pdf_name)
text = parsed['content']

if text:
    new_str = re.sub("\n", "", text)
    new_str = re.sub(" ", "", new_str)

    spacing = Spacing()
    kospacing_result = spacing(new_str)
```
<br/>

- 멀티 쓰레딩으로 크롤링 수행
```python
with ThreadPoolExecutor(max_workers=10) as page_executor:
    futures = [page_executor.submit(process_page, page) for page in range(1, pages + 1)]
    for future in as_completed(futures):
        future.result()
```
<br/>

