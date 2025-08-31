# 뉴스 크롤러 시스템

연합뉴스, 이데일리, 인포맥스 금융 뉴스 수집 시스템
- 이데일리: 직접 사이트 크롤링 (2014-2025)
- 인포맥스: 직접 사이트 크롤링 (2014-2025)
- 연합뉴스: API 크롤링 (2016-2025), 네이버는 차단됨

## 디렉토리 구조

```
crawler/
├── core/                           # 핵심 크롤러 모듈
│   ├── base_crawler.py            # 기본 크롤러 클래스
│   └── safe_crawler.py            # 안전 모드 크롤러 (차단 우회)
├── scripts/                        
│   └── run.py                     # 통합 실행 스크립트
├── data/
│   ├── unified/                   # 일반 모드 데이터
│   └── safe/                      # 안전 모드 데이터
└── logs/                          # 로그 파일
```

## 빠른 시작

### 2015년 데이터 수집 (권장)
```bash
cd crawler/scripts
python run.py yearly 2015 --safe   # 안전 모드로 2015년 전체 수집
```

### 테스트 실행
```bash
python run.py test                  # 최근 3일 테스트
python run.py test --safe           # 안전 모드 테스트
```

## 실행 방법

### 1. 테스트 실행 (최근 3일)
```bash
cd crawler/scripts
python run.py test                  # 일반 모드
python run.py test --safe           # 안전 모드
```

### 2. 월별 크롤링
```bash
python run.py monthly 2015 1        # 2015년 1월
python run.py monthly 2015 1 --safe # 안전 모드
```

### 3. 연도별 크롤링
```bash
python run.py yearly 2015           # 2015년 전체
python run.py yearly 2015 --safe    # 안전 모드 (권장)
```

### 4. 크롤링 재개 (중단된 지점부터)
```bash
python run.py resume 2015 7         # 2015년 7월부터 재개
python run.py resume 2015 7 --safe  # 안전 모드
```

### 5. 데이터 병합
```bash
python run.py merge                 # 수집된 데이터 병합
```

## 모드 설명

### 일반 모드 (기본)
- 빠른 속도로 데이터 수집
- 대기시간: 1초
- 적합한 경우: 소량 테스트, 빠른 수집이 필요한 경우

### 안전 모드 (--safe)
- 네이버 검색 제한 우회를 위한 강화된 안전장치
- 특징:
  - 랜덤 대기시간 (2-5초)
  - User-Agent 로테이션 (10개 브라우저/OS 조합)
  - 자동 재시도 메커니즘 (exponential backoff)
  - 주기적 세션 재생성
  - 월별 수집 간 긴 휴지시간 (60-120초)
- 권장 사용: 대량 데이터 수집, 연도별 크롤링

## 명령어 옵션

### 공통 옵션
- `--safe`: 안전 모드 활성화
- `--log FILE`: 로그 파일 경로 지정 (기본: crawler.log)

### 소스 지정
```bash
python run.py yearly 2015 --sources yonhap,edaily  # 특정 소스만
```

### 기간 지정
```bash
python run.py yearly 2015 --start-month 1 --end-month 6  # 상반기만
```

## 데이터 형식

### 수집 데이터 (JSON)
```json
{
  "yonhap": [...],
  "edaily": [...],
  "infomax": [...]
}
```

### 기사 구조
```json
{
  "title": "제목",
  "content": "본문 내용",
  "date": "2015-01-01",
  "url": "기사 URL",
  "source": "yonhap/edaily/infomax",
  "keyword": "금리",
  "content_length": 1234
}
```

## 주의사항

1. **네이버 검색 제한**: 대량 수집 시 반드시 `--safe` 옵션 사용
2. **시간 소요**: 안전 모드로 1년치 수집 시 약 6-8시간 소요
3. **중단 시 재개**: `resume` 명령으로 중단된 월부터 재개 가능
4. **데이터 저장**: 
   - 일반 모드: `data/unified/`
   - 안전 모드: `data/safe/`

## 문제 해결

### 네이버 검색 차단 시
1. 안전 모드 사용: `--safe`
2. 차단 지속 시: 24시간 대기 후 재시도
3. VPN/프록시 사용 고려

### 수집 실패 시
1. 로그 확인: `crawler.log`
2. 네트워크 상태 확인
3. 특정 월만 재수집: `monthly` 명령 사용

## 예시 워크플로우

### 2015년 전체 데이터 수집
```bash
# 1. 안전 모드로 전체 수집
python run.py yearly 2015 --safe

# 2. 중단된 경우 7월부터 재개
python run.py resume 2015 7 --safe

# 3. 수집 완료 후 데이터 병합
python run.py merge

# 4. 결과 확인
ls -la ../data/safe/
cat ../data/safe/summary_2015.json
```

## 기타 크롤러

### MPB 의사록 (`crawler/MPB/`)
- 한국은행 금융통화위원회 의사록
- 수집량: 약 200건 (2014-2025)
- 페이지: 30페이지 크롤링 (최적화됨)
- PDF 텍스트 추출 후 토의내용/심의결과 파싱

### 채권 보고서 (`crawler/BOND/`)
- 네이버 금융 증권사 채권 분석 보고서
- 수집량: 약 5,900건 (2014-2025)
- 멀티스레딩 지원 (10 workers)
- PDF → CSV 변환, PyPDF2 사용

### 콜금리 (`crawler/call_ratings/`)
- 대한상공회의소 일별 콜금리 데이터
- 2014-2025년 일별 데이터

### 금리 데이터 (`crawler/interest_rates/`)
- 한국은행 기준금리 변경 내역
- JavaScript 변수에서 직접 추출

## 예상 수집 성능
- 연합뉴스: 2016년부터만 가능, 페이지네이션으로 모든 기사 수집
- 이데일리: 수집 중 (기존 데이터 재수집 진행)
- 인포맥스: 월 400-900개 (안정적)
- MPB: 연 20개 회의록
- 채권: 월 500개 보고서