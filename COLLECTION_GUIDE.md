# 데이터 수집 가이드 및 로직 수정 방법

## 🔴 문제점 분석

### 1. MPB 크롤러 문제점

#### 🐛 주요 버그: 페이지 수 제한
```python
# 현재 코드 (mpb_crawler_perfect.py:58-66)
if self.start_year >= 2024:
    self.total_pages = 10  # ❌ 너무 적음!
elif self.start_year >= 2020:
    self.total_pages = 30  # ❌ 부족!
else:
    self.total_pages = 50  # ❌ 여전히 부족!
```

**문제**: 한국은행 사이트는 페이지당 10개씩 표시하므로, 50페이지는 최대 500개만 수집 가능. 하지만 실제로는 더 많은 페이지가 있을 수 있음.

#### 🛠 해결 방법 1: 페이지 수 증가
```python
# 수정된 코드
if self.start_year >= 2024:
    self.total_pages = 30   # 300개까지
elif self.start_year >= 2020:
    self.total_pages = 50   # 500개까지
else:
    self.total_pages = 100  # 1000개까지 (충분!)
```

#### 🛠 해결 방법 2: 동적 페이지 감지 (더 나은 방법)
```python
def parse_first_page(self, response):
    """첫 페이지에서 실제 전체 페이지 수 파악"""
    
    # 페이지네이션에서 마지막 페이지 번호 찾기
    last_page = response.css('div.paging a:last-child::text').get()
    if not last_page:
        # 대체 방법: onclick 속성에서 페이지 번호 추출
        last_page_link = response.css('a[onclick*="pageIndex"]:last-child::attr(onclick)').get()
        if last_page_link:
            import re
            match = re.search(r'pageIndex[\'"]?\s*:\s*(\d+)', last_page_link)
            if match:
                last_page = match.group(1)
    
    if last_page:
        self.total_pages = int(last_page)
        self.logger.info(f"🎯 실제 전체 페이지 수: {self.total_pages}개")
    else:
        # 기본값 사용
        self.total_pages = 100
        self.logger.warning(f"⚠️ 마지막 페이지를 찾을 수 없어 기본값 {self.total_pages} 사용")
```

---

### 2. 채권 크롤러 문제점

#### 🐛 문제: 단일 스레드로 너무 느림
현재 `bond_crawling.py`는 멀티스레딩을 지원하지만 기본적으로 순차 처리

#### 🛠 해결: 병렬 처리 활성화
```python
# 현재는 주석 처리되어 있는 부분을 활성화
from concurrent.futures import ThreadPoolExecutor, as_completed

# 메인 실행 부분에 추가
def run_parallel_crawling(pages, max_workers=10):
    """병렬 크롤링 실행"""
    all_results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 각 페이지를 병렬로 처리
        futures = []
        for page in range(1, pages + 1):
            url = f"https://finance.naver.com/research/debenture_list.naver?...&page={page}"
            future = executor.submit(process_page, url)
            futures.append(future)
        
        # 결과 수집
        for future in as_completed(futures):
            try:
                result = future.result()
                all_results.extend(result)
            except Exception as e:
                print(f"Error: {e}")
    
    return all_results
```

---

## 🚀 수집 실행 방법

### 1. MPB 의사록 수집 (수정 후)

#### Step 1: 크롤러 파일 수정
```bash
# 1. 파일 열기
nano crawler/MPB/mpb_crawler/spiders/mpb_crawler_perfect.py

# 2. 58-66번 라인의 페이지 수 변경
# self.total_pages = 10 → self.total_pages = 100
```

#### Step 2: 누락된 의사록만 수집
```bash
cd crawler/MPB

# 전체 재수집 (권장)
/opt/anaconda3/envs/ds_env/bin/scrapy crawl mpb_crawler_perfect \
    -a start_year=2014 \
    -a end_year=2025 \
    -o ../../data/mpb_complete_2014_2025.json \
    -s CLOSESPIDER_PAGECOUNT=200 \
    -s LOG_LEVEL=INFO
```

#### Step 3: 결과 확인
```bash
# 수집된 개수 확인
cat ../../data/mpb_complete_2014_2025.json | grep -c '"title"'
```

---

### 2. 채권 리포트 수집

#### Step 1: 날짜별 분할 수집 (월 단위 권장)
```bash
cd crawler/BOND

# 2024년 1월 수집 예시
/opt/anaconda3/envs/ds_env/bin/python bond_crawling.py 2024-01-01 2024-01-31

# 2024년 2월 수집
/opt/anaconda3/envs/ds_env/bin/python bond_crawling.py 2024-02-01 2024-02-28
```

#### Step 2: 자동화 스크립트 생성
```bash
# collect_bonds.sh 파일 생성
cat > collect_bonds.sh << 'EOF'
#!/bin/bash

# 연도별 수집
for year in 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025; do
    for month in 01 02 03 04 05 06 07 08 09 10 11 12; do
        # 월의 마지막 날 계산
        if [ $month -eq 12 ]; then
            end_day=31
        elif [ $month -eq 02 ]; then
            end_day=28
        elif [ $month -eq 04 ] || [ $month -eq 06 ] || [ $month -eq 09 ] || [ $month -eq 11 ]; then
            end_day=30
        else
            end_day=31
        fi
        
        start_date="${year}-${month}-01"
        end_date="${year}-${month}-${end_day}"
        
        echo "수집 중: $start_date ~ $end_date"
        /opt/anaconda3/envs/ds_env/bin/python bond_crawling.py $start_date $end_date
        
        # 30초 대기 (서버 부하 방지)
        sleep 30
    done
done
EOF

chmod +x collect_bonds.sh
```

#### Step 3: 백그라운드 실행
```bash
# 백그라운드에서 실행
nohup ./collect_bonds.sh > bond_collection.log 2>&1 &

# 진행상황 모니터링
tail -f bond_collection.log
```

---

## 🔍 수집 상태 확인 방법

### MPB 의사록 확인
```python
# check_mpb.py
import json

with open('data/mpb_complete_2014_2025.json', 'r') as f:
    data = json.load(f)

# 연도별 집계
from collections import defaultdict
year_counts = defaultdict(int)

for item in data:
    title = item.get('title', '')
    if '년도' in title:
        year = title.split('년도')[0].split('(')[-1]
        try:
            year_counts[int(year)] += 1
        except:
            pass

# 누락 확인
for year in range(2014, 2026):
    expected = 24  # 연간 약 24회
    actual = year_counts.get(year, 0)
    if actual < expected:
        print(f"{year}년: {actual}/{expected} (누락: {expected-actual}개)")
```

### 채권 리포트 확인
```bash
# PDF 파일 개수
find . -name "*.pdf" | wc -l

# CSV 파일 개수
find dataset_2 -name "*.csv" | wc -l

# 날짜별 분포 확인
ls -la *.pdf | awk '{print $6, $7}' | sort | uniq -c
```

---

## ⚠️ 주의사항

1. **서버 부하 방지**
   - 요청 간 최소 1-2초 대기
   - 동시 스레드 10개 이하 유지

2. **에러 처리**
   - PDF 파싱 실패 시 건너뛰기
   - 네트워크 타임아웃 30초 설정

3. **중복 방지**
   - 이미 수집된 파일은 건너뛰기
   - URL 기반 중복 체크

---

## 📊 예상 소요 시간

| 작업 | 예상 시간 | 비고 |
|------|----------|------|
| MPB 누락분 수집 | 1-2시간 | 64개 |
| 채권 리포트 (1년) | 2-3시간 | 약 2,500개 |
| 채권 리포트 (전체) | 24-36시간 | 약 30,000개 |

**권장**: 채권 리포트는 백그라운드에서 실행하면서 다른 작업 병행

---

## 🎯 즉시 실행 명령어

```bash
# 1. MPB 수집 (터미널 1)
cd ~/Desktop/my_git/mpb-stance-mining/crawler/MPB
/opt/anaconda3/envs/ds_env/bin/scrapy crawl mpb_crawler_perfect -a start_year=2014 -a end_year=2025 -o ../../data/mpb_fixed.json -s CLOSESPIDER_PAGECOUNT=200

# 2. 채권 리포트 수집 (터미널 2)
cd ~/Desktop/my_git/mpb-stance-mining/crawler/BOND
/opt/anaconda3/envs/ds_env/bin/python bond_crawling.py 2024-01-01 2024-12-31
```