# 논문 재현 통합 크롤러 사용 가이드 (최종 버전)

## 🔄 업데이트 내용 (2025-08-25)

### 주요 변경사항
- **기간 조정**: 2005-2017 → **2014-2025** (데이터 접근성 고려)
- **동적 크롤링**: 브라우저 화면 표시 기능 추가
- **성능 개선**: 타임아웃 15분으로 연장, 더 많은 데이터 수집 가능

---

## 📊 데이터 수집 범위

- **연구 기간**: 2014년 1월 ~ 2025년 8월 (11년간)
- **키워드**: "금리"
- **수집 대상**:
  - 연합뉴스 (목표 25%)
  - 이데일리 (목표 33%)  
  - 연합인포맥스 (목표 42%)
  - MPB 회의록 (전체 기간)
  - 채권 분석 리포트
  - 콜금리 데이터

---

## 🚀 실행 방법

### 1. 테스트 모드 (빠른 확인 - 권장)
```bash
cd /Users/lord_jubin/Desktop/my_git/mpb-stance-mining/crawler/scripts
/opt/anaconda3/envs/ds_env/bin/python final_paper_reproduction_crawler_2014_2025.py --test
```
- **수집 범위**: 2025년 3-8월 (최근 6개월)
- **수집량**: 각 소스당 최대 100개
- **예상 시간**: 30분 내외

### 2. 동적 크롤링 화면 표시 (진행 상황 확인)
```bash
# 테스트 모드 + 브라우저 화면 표시
/opt/anaconda3/envs/ds_env/bin/python final_paper_reproduction_crawler_2014_2025.py --test --show-browser

# 전체 수집 + 브라우저 화면 표시
/opt/anaconda3/envs/ds_env/bin/python final_paper_reproduction_crawler_2014_2025.py --show-browser
```
- **실시간 진행 상황** 확인 가능
- 크롤러가 어떤 페이지를 수집하는지 볼 수 있음

### 3. 전체 수집 모드 (대규모 연구용)
```bash
/opt/anaconda3/envs/ds_env/bin/python final_paper_reproduction_crawler_2014_2025.py
```
- **수집 범위**: 2014년 1월 ~ 2025년 8월 전체
- **수집량**: 각 소스당 최대 2000개
- **예상 시간**: 수 시간 ~ 수일

---

## 📁 출력 위치 및 파일

### 메인 출력 디렉토리
`/crawler/data/paper_reproduction/`

### 출력 파일 형식
- **월별 뉴스 데이터**:
  - `yonhap_YYYY_MM.json`: 연합뉴스 월별 데이터
  - `edaily_YYYY_MM.json`: 이데일리 월별 데이터
  - `infomax_YYYY_MM.json`: 인포맥스 월별 데이터

- **기타 데이터**:
  - `mpb_minutes.json`: MPB 회의록
  - `call_rates.json`: 콜금리 데이터
  - `collection_progress.json`: 수집 진행 상황
  - `collection_report.txt`: 최종 수집 리포트

---

## 🎯 성능 개선사항

### 타임아웃 연장
- **전체 모드**: 15분 (기존 10분에서 연장)
- **테스트 모드**: 5분

### 에러 처리 개선
- JSON 파싱 오류 처리
- 개별 크롤러 실패 시에도 다른 크롤러 계속 진행
- 상세한 오류 로깅

### 실시간 모니터링
- `--show-browser` 옵션으로 크롤링 과정 실시간 확인
- 콘솔에 실시간 진행 상황 출력

---

## 🔍 개별 크롤러 테스트

### InfoMax 크롤러 (가장 안정적)
```bash
cd /Users/lord_jubin/Desktop/my_git/mpb-stance-mining/crawler/InfoMax/infomax_crawler
/opt/anaconda3/envs/ds_env/bin/scrapy crawl infomax_fixed \
  -a start_date=2024-01-01 \
  -a end_date=2024-01-31 \
  -s CLOSESPIDER_ITEMCOUNT=10 \
  -o test_output.json
```

### Yonhap 크롤러 (개선된 네이버 검색 방식)
```bash
cd /Users/lord_jubin/Desktop/my_git/mpb-stance-mining/crawler/yh/yh_crawler
/opt/anaconda3/envs/ds_env/bin/scrapy crawl yh_fixed \
  -a start_date=2024-01-01 \
  -a end_date=2024-01-31 \
  -s CLOSESPIDER_ITEMCOUNT=10 \
  -o test_output.json
```

### 콜금리 크롤러 (가장 빠름)
```bash
cd /Users/lord_jubin/Desktop/my_git/mpb-stance-mining/crawler/call_ratings/call_ratings_crawler
/opt/anaconda3/envs/ds_env/bin/scrapy crawl call_ratings \
  -s CLOSESPIDER_ITEMCOUNT=50 \
  -o test_output.json
```

---

## 🎨 새로운 기능들

### 1. 브라우저 화면 표시
- 동적 크롤링 과정을 실시간으로 확인
- 어떤 페이지를 방문하는지, 어떤 데이터를 수집하는지 볼 수 있음

### 2. 개선된 통계 분석
- 실시간 언론사별 비율 추적
- 목표 비율(인포맥스 42%, 이데일리 33%, 연합뉴스 25%) 대비 달성률 표시

### 3. 더 나은 날짜 범위
- 2014-2025: 데이터 접근이 확실한 기간
- 최근 데이터로 테스트 시 높은 성공률 보장

---

## ⚠️ 주의사항

### 데이터 가용성
- **2024-2025년**: 최고의 데이터 품질
- **2020-2023년**: 양호한 데이터 품질  
- **2014-2019년**: 일부 제약 있을 수 있음

### 권장 실행 순서
1. **첫 실행**: `--test` 모드로 동작 확인
2. **문제 발생 시**: `--test --show-browser`로 문제 진단
3. **안정 확인 후**: 전체 수집 실행

### 시스템 리소스
- 동시에 여러 크롤러 실행 시 CPU/메모리 사용량 높음
- 브라우저 표시 모드는 추가 리소스 필요

---

## 📞 문제 해결

### 크롤러가 0개 수집하는 경우
```bash
# 최신 데이터로 개별 테스트
cd InfoMax/infomax_crawler
/opt/anaconda3/envs/ds_env/bin/scrapy crawl infomax_fixed -a start_date=2024-08-01 -a end_date=2024-08-31 -s CLOSESPIDER_ITEMCOUNT=5
```

### 타임아웃 발생하는 경우
- 인터넷 연결 확인
- VPN 사용 중이라면 해제 후 재시도
- 테스트 모드로 먼저 확인

### 브라우저 화면이 나타나지 않는 경우  
- 시스템에 GUI 환경이 필요
- SSH 연결 시에는 X11 포워딩 필요

---

## 🏁 기대 결과

### 테스트 모드 (2025년 3-8월)
- **예상 수집량**: 300-1000개
- **소요 시간**: 20-40분
- **성공률**: 90% 이상

### 전체 모드 (2014-2025)
- **예상 수집량**: 50,000-200,000개
- **소요 시간**: 6-24시간  
- **성공률**: 70-80%

이제 더 안정적이고 많은 데이터를 수집할 수 있는 환경이 준비되었습니다! 🎉