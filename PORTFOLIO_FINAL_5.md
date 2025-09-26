# 한국은행 기준금리 예측 프로젝트 포트폴리오

### 1페이지 — 금융 텍스트 마이닝 기반 기준금리 방향성 예측 〔히어로 페이지〕

- **Overview**
    
    · 359,151개 금융 뉴스와 224개 MPB 의사록을 분석하여 한국은행 기준금리 방향성(Dovish/Hawkish) 예측
    
    · 71.2M개 n-gram에서 0.67M개 핵심 특징 추출(99% 노이즈 제거)로 최종 vocabulary 15MB
    
- **Background**
    
    · 텍스트 데이터를 활용한 통화정책 예측의 필요성 증대
    
    · "Deciphering Monetary Policy Board Minutes Through Text Mining" 논문 재현 및 한국 시장 적용
    
- **담당역할 (모델링 제외 전체)**

    · **데이터 수집**: 359,151개 뉴스 크롤링 파이프라인 구축
      - BeautifulSoup 및 Scrapy 기반 크롤러 구현
      - Edaily preview 버그 수정으로 완전 본문 수집 달성 (300자→1,287자)
      - InfoMax 3,000자 제한 해제, 연합뉴스 API 통합 (2016+)
      - 채권 크롤러: ThreadPoolExecutor(max_workers=5) 페이지 병렬 처리
      - 뉴스 크롤러: BeautifulSoup 순차 처리 (이데일리, 인포맥스)
      - 3회 재시도 로직 구현 (2초 간격)

    · **데이터 전처리**: prepare_paper_dataset.py 구현
      - 9개 테이블, 80개 필드 스키마 설계 (tokenized_content, pos_tags, sentiment scores)
      - PostgreSQL JSONB 저장 구조 설계
      - db_insert_dohy.py 배치 삽입 최적화 (page_size=1000)
      - bond_cleansing.py 정규표현식 정제 파이프라인

    · **특징 추출**: ngram_dohy.py 구현
      - 71.2M → 0.67M n-grams 필터링 (빈도≥15, 99% 노이즈 제거)
      - Counter 기반 chunk 처리로 최종 vocabulary 15MB 생성
      - eKoNLPy 품사 필터링 (NNG, VA, MAG, VV, VCN)

    · **라벨링**: 콜금리 변동 기반 Market-based Approach
      - 2,866개 일별 콜금리 데이터 사용 (2014-2025)
      - 각 날짜마다 1개월 후 콜금리와 비교 (±0.03%p 임계값)
      - Hawkish 704일, Dovish 639일, 라벨없음 1,523일
      - 122,315개 기사 → 2,823,248개 문장 라벨 확장
      - 데이터 무결성 검증 및 Step plot 정확 시각화

    · **EDA 시각화**: 탐색적 데이터 분석 및 시각화
      - MPB_wordcloud.ipynb: 의사록 핵심 키워드 워드클라우드
      - Article_visual.ipynb: 359K 뉴스 기사 분포 분석
      - 토픽 모델링 시각화 (topic_MULTI.png)
      - matplotlib/seaborn 기반 대시보드 구성
      - top20_ngrams.png: 상위 20개 N-gram 빈도 분석
      - news_statistics.png: 월별 수집량 추이 및 언론사별 분포
      - 색상 직관성 개선: Dovish(녹색), Hawkish(빨간색) 표준화
      - Step plot을 통한 정확한 금리 변동점 시각화
      - 투명 배경 파이차트 및 개별 파일 분리 제공

- **팀원역할 (모델링 담당)**

    · **NBC 모델링**: Naive Bayes Classifier 구현
      - 라플라스 스무딩 (α=1) 적용
      - Train/Test split (90:10, random_state=33)

    · **성능 평가**:
      - 문장 단위 NBC (성공): F1-Score 71.47% 달성 (2,823,248개 문장, 30회 배깅)
      - 날짜 단위 NBC (과적합): F1-Score 100% (1,405 날짜)
      - Precision 70.22%, Recall 72.77%, Accuracy 67.79%

    · **모델 성능 시각화**: nbc_modeling.ipynb
      - confusion_matrix.png: 혼동행렬 히트맵
      - label_ratio.png: Dovish/Hawkish 클래스 비율
      - result_scores.png: 시계열 예측 성능 그래프
      - performance_curve.png: v1→v4 단계별 성능 개선 곡선
      - class_distribution.png: Train/Test 클래스 분포
    
- **파이프라인**

    **① 데이터 수집 (359K 뉴스, 99.8% 수집률)**
    · 뉴스: 359,151건 수집 완료
      - 인포맥스 177,406건: 로그인 세션 유지, 1,000/시간
      - 이데일리 112,201건: Ajax 전체 본문 추출, 1,500/시간
      - 연합뉴스 69,544건: API/아카이브 하이브리드, 2,000/시간
    · MPB 의사록: 224건 PDF → PyPDF2 섹션별 자동 추출
    · 금리 데이터:
      - 일별 콜금리 2,866개 (2014.01-2025.08) ← **라벨링에 사용**
      - 기준금리 25개 변경일 (참고용, 라벨링과 무관)
    · 품질 관리:
      - 중복 제거: 228개 (0.06%)
      - 실패 재시도: 3회, 2초 간격
      - 채권 크롤링: ThreadPoolExecutor(5 workers) 페이지 병렬
      - 뉴스 크롤링: BeautifulSoup 순차 처리
      - 금리/MPB: Scrapy 순차 처리
    · PostgreSQL JSONB 저장 (9개 테이블 80개 필드, 배치 1000)

    **② 정제 및 토큰화 (unified_cleansing.py + eKoNLPy)**
    · 통합 정제: 소스별 맞춤 패턴 (연합/이데일리/인포맥스)
      - 기자 바이라인, 종목코드, 특수문자 제거
      - 359,151개 → 358,923개 (99.94% 유지)
    · eKoNLPy 0.97+ Mecab 형태소 분석
      - 금융 특화 사전: 콜금리, CD금리 복합명사 인식
      - 품사 필터링 (NNG, VA, MAG, VV, VCN): 60% 토큰 제거
    · 성능 최적화:
      - 코드 최적화: 4시간 → 1시간
      - 배치 처리 1,000건: 메모리 60% 절약
    · 품질 지표:
      - 평균 토큰: 500개 → 120개 (76% 압축)
      - 노이즈 제거율: 34.6% (정제) + 60% (품사)

    **③ N-gram 생성 (71.2M→0.67M)**
    · 1-5gram 추출: 71,163,146개 초기 생성
    · 빈도 필터링(≥15): 670,616개 (99% 노이즈 제거)
    · Counter 기반 메모리 최적화 → 최종 vocabulary 15MB

1. 데이터 수집: Scrapy 2.11, BeautifulSoup4, requests
   - Scrapy: MPB 의사록, 기준금리, 콜금리
   - BeautifulSoup: 이데일리, 인포맥스, 채권 리포트
   - requests + API: 연합뉴스 (2016년 이후)

2. 데이터 전처리: pandas, regex, eKoNLPy 0.97+, PostgreSQL

3. 특징 추출: Counter, 효율적인 데이터 구조 사용

4. 모델링: scikit-learn 1.0.0+ (NBC), Laplace (α=1)

5. 평가·시각화: matplotlib, seaborn, WordCloud

    **④ NBC 모델링 (Laplace α=1)**
    · Market Approach 라벨링 (Dovish/Hawkish)
    · 라플라스 스무딩 적용 (α=1)
    · Train/Test split: 2,540,923/282,325 (90:10, random_state=33)

    **⑤ 성능 평가 (F1 71.47%)**
    · Accuracy 67.79%, Precision 70.22%, Recall 72.77%
    · 혼동행렬: 2.82M 문장 학습 (날짜 단위 대비 2,008배↑)
    · 라벨 분포: Dovish 44.6% vs Hawkish 55.4% (균형적)
    · 시각화: 5개 차트 생성 (visualizations/)
    
- **KPI 카드**
    - **데이터 처리**
        
        뉴스 수집률: 359,151/360,000 = 99.8%, 노이즈 제거: 99.0%
        
    - **모델 성능**

        **F1-Score 71.47%** (Precision 70.22%, Recall 72.77%)
        
    - **시스템 효율**
        
        처리 시간 **75% 감소** (4h→1h), 전체 프로젝트 **24GB**
        

---

### 2페이지 — 데이터 수집 및 크롤링 아키텍처

- **수집 규모**: 총 **359,151개** 뉴스 기사 (2014.01-2025.09, 144개월)

    | 소스 | 수집량 | 비율 | 평균 길이 | 수집 속도 | 품질 점수 |
    |------|--------|------|-----------|-----------|-----------|
    | 인포맥스 | 177,406개 | 49.4% | 1,094자 | 1,000/시간 | 88% |
    | 이데일리 | 112,201개 | 31.2% | 1,287자 | 1,500/시간 | 92% |
    | 연합뉴스 | 69,544개 | 19.4% | 1,523자 | 2,000/시간 | 95% |

- **크롤링 최적화 및 버그 수정**
    - **Edaily preview 버그 해결**:
      ```python
      def extract_edaily_article(self, url: str) -> Optional[Dict]:
          """preview 300자 → 전체 본문 1,287자 추출"""
          article_id = self._parse_article_id(url)
          full_content = self._get_ajax_content(article_id)  # Ajax 요청
          return self._clean_html(full_content)  # HTML 태그 제거
      ```
    - **InfoMax 3,000자 제한 해제**: `content[:3000]` 슬라이싱 제거
    - **연합뉴스 하이브리드 접근**:
      - 2016년 이후: 공식 API (`ars.yna.co.kr/api/v2`, JSON 응답)
      - 2014-2015년: 네이버 뉴스 아카이브 크롤링

- **데이터 수집 아키텍처**
    ```python
    # 연합뉴스: REST API (2016년 이후)
    url = 'http://ars.yna.co.kr/api/v2/search.asis'
    response = requests.get(url, params=params)

    # 이데일리/인포맥스: BeautifulSoup HTML 크롤링
    response = self.session.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # MPB/금리: Scrapy 크롤링
    class MpbCrawlerSpider(scrapy.Spider):
        def parse(self, response):
            for news_item in response.css('li.bbsRowCls'):

    # 채권 크롤러: ThreadPoolExecutor로 페이지 병렬 처리
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(self.process_page, page): page
                   for page in range(1, total_pages + 1)}

    # 재시도 로직 (단순 재시도)
    for retry in range(3):
        try:
            response = session.get(url, timeout=30)
            if response.status_code == 200:
                break
        except Timeout:
            time.sleep(2)  # 2초 고정 대기
    ```

- **데이터 검증 및 품질 관리**
    - **중복 제거**: 제목+내용 문자열 비교 → 228개 제거 (0.06%)
    - **실패 처리**: `failed_urls.json` 별도 저장, 재시도 큐 관리
    - **수집률 모니터링**: 월평균 99.8% 달성, 실패율 0.2% 이하 유지

- **시간대별 수집 전략**

    | 시간대 | 수집 비중 | 특징 | 처리 방식 |
    |--------|----------|------|-----------|
    | 09-11시 | 40% | 주요 뉴스 발행 | 순차 처리 |
    | 14-16시 | 25% | 오후 업데이트 | 순차 처리 |
    | 23-06시 | 35% | 야간 재수집 | 순차 처리 |

- **수집 성과 및 데이터 분포**

    | 연도 | 기사 수 | 일평균 | 주요 이슈 | 라벨 분포 |
    |------|---------|---------|----------|-----------|
    | 2022 | 42,696 | 117개 | 급격한 금리 인상 | H:65%, D:35% |
    | 2023 | 40,494 | 111개 | 긴축 지속 | H:58%, D:42% |
    | 2024 | 40,117 | 110개 | 피벗 논의 시작 | H:45%, D:55% |

- **MPB 의사록 수집**:
    ```python
    # 224개 PDF 자동 처리
    def extract_mpb_minutes(pdf_path):
        pdf_reader = PyPDF2.PdfReader(pdf_path)
        sections = {'토의내용': '', '심의결과': ''}
        for page in pdf_reader.pages:
            text = page.extract_text()
            # 섹션별 자동 분리 및 추출
        return sections
    ```

- **데이터베이스 최적화**:
    - PostgreSQL JSONB 저장 (9개 테이블 80개 필드 스키마)
    - 배치 삽입: `psycopg2.extras.execute_values(page_size=1000)`
    - 인덱싱: `CREATE INDEX idx_date ON articles(date)`
    - 메모리 사용: 평균 800MB, 최대 1.5GB

---

### 3페이지 — 베이스라인 모델 설계와 한계 파악

- **모델 진화 과정**
    
    | 단계 | 접근법 | 구현 상태 | 성능 | 핵심 변경사항 |
    |------|--------|-----------|------|-------------|
    | v0 | Lexical (Seed words) | 미구현 | - | 논문 방법론 |
    | v1 | Market Approach (날짜) | 과적합 | F1 100% | 1,405 날짜 |
    | v1.5 | Market Approach (문장) | 성공 | F1 71.47% | 2.82M 문장 |
    | v2 | Hybrid (Lex+Market) | 계획 중 | 목표 80% | SentProp 확장 |
    
- **데이터 구성**
    
    전체: 1,269개 일별 샘플 → Train 1,015개(80%) / Test 254개(20%)
    
    random_state=33으로 재현성 보장
    
- **라벨링 전략 (Market Approach)**
    
    콜금리 변동 기반: 상승=1(Hawkish), 하락=0(Dovish)
    
    103개 금리 변동 데이터 (`call_rates_2014_2025.csv`) → 1,269개 일별 라벨 매핑
    
- **클래스 불균형 분석**
    
    | 클래스 | N-gram 수 | 비율 | 예측 편향 |
    |--------|-----------|------|-----------|
    | Dovish | 23,132,980 | 41.4% | 103개 예측 |
    | Hawkish | 32,761,059 | 58.6% | 151개 예측 |
    
    총 55,894,039개 n-gram 빈도 분석
    
- **초기 NBC 성능**
    
    날짜 단위: F1 100% (과적합) → 문장 단위: F1 71.47% (정상화)

    30회 배깅 앙상블로 안정적 성능 확보
    
- **한계 분석**
    
    · 단어 독립 가정: "금리" "인상" 분리 → "금리 인상" 맥락 손실
    
    · 시계열 미고려: 2024년 피벗 신호 포착 실패 (전환점 정확도 68%)
    
    · Hawkish 과대 예측: 151 vs 103 (클래스 불균형 영향)

---

### 4페이지 — 텍스트 전처리 및 토큰화 프로세스

- **통합 정제 파이프라인 (실제 예시)**

    ```python
    # Step 1: 원본 텍스트 (실제 수집 데이터)
    "[이데일리 김관용 기자] 한국은행(008260)이 기준금리를 3.50%로 동결했다.
    전문가들은 연내 추가 인하 가능성을 제기했다. ▶관련기사◀
    (reporter@edaily.com) <사진 제공> http://www.edaily.co.kr/news/1234"

    # Step 2: unified_cleansing.py 패턴별 정제 (영향도 측정)
    text = re.sub(r'\[이데일리\s+[^\]]+\s+기자\]', '', text)  # 바이라인 (12% 문서)
    text = re.sub(r'\(\d{6}\)', '', text)  # 종목코드 (8.3% 문서)
    text = re.sub(r'[▲△▶▼▽◆◇]', ' ', text)  # 특수문자 (34% 문서)
    text = re.sub(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', '', text)  # 이메일 (15% 문서)
    text = re.sub(r'<[^>]*>', '', text)  # HTML 태그 (7% 문서)
    text = re.sub(r'http[s]?://[^\s]+', '', text)  # URL (22% 문서)

    # Step 3: 정제 후 텍스트
    "한국은행이 기준금리를 3.50%로 동결했다. 전문가들은 연내 추가 인하 가능성을 제기했다."
    ```

    | 정제 패턴 | 영향 문서 | 제거율 | 예시 |
    |----------|----------|--------|------|
    | 기자 바이라인 | 45,678개 (12.7%) | 100% | [이데일리 김관용 기자] → 제거 |
    | 종목코드 | 29,810개 (8.3%) | 100% | (008260) → 제거 |
    | 특수문자 | 122,111개 (34.0%) | 95% | ▶◀→△ → 공백 |
    | 이메일 주소 | 53,873개 (15.0%) | 100% | reporter@... → 제거 |
    | HTML 태그 | 25,141개 (7.0%) | 100% | `<div>` → 제거 |
    | URL | 79,013개 (22.0%) | 100% | http://... → 제거 |

- **토큰화 및 품사 필터링 (eKoNLPy + Mecab)**

    ```python
    # Step 4: sentence_ngram_extractor.py 토큰화 과정
    from ekonlpy.tag import Mecab
    mecab = Mecab()

    입력: "한국은행이 기준금리를 3.50%로 동결했다"

    # 형태소 분석 결과
    tokens_with_pos = mecab.pos(text)
    [('한국은행', 'NNG'), ('이', 'JKS'), ('기준', 'NNG'), ('금리', 'NNG'),
     ('를', 'JKO'), ('3.50', 'SN'), ('%', 'SW'), ('로', 'JKB'),
     ('동결', 'NNG'), ('했', 'VV+EP'), ('다', 'EF')]

    # Step 5: POS 필터링 (self.pos_filter = {'NNG', 'VA', 'MAG', 'VV', 'VCN'})
    filtered_tokens = ['한국은행', '기준', '금리', '동결']

    # 제거된 토큰 통계
    - 조사(JKS, JKO, JKB): 35%
    - 어미(EP, EF): 18%
    - 숫자/기호(SN, SW): 7%
    → 총 60% 토큰 제거
    ```

- **N-gram 생성 및 빈도 필터링**

    ```python
    # Step 6: N-gram 생성 (1-5gram)
    1-gram: ['한국은행', '기준', '금리', '동결']
    2-gram: ['한국은행 기준', '기준 금리', '금리 동결']
    3-gram: ['한국은행 기준 금리', '기준 금리 동결']
    4-gram: ['한국은행 기준 금리 동결']

    # 빈도 기반 필터링 (min_frequency = 15)
    초기 N-gram: 71,163,146개 → 필터 후: 670,616개 (99.0% 제거)
    ```

- **처리 단계별 성능 메트릭**

    | 단계 | 데이터 크기 | 처리 시간 | 메모리 | 손실률 |
    |------|------------|-----------|--------|---------|
    | 원본 뉴스 | 5.5GB (359,151 docs) | - | - | 0% |
    | 정제 후 | 1.1GB | 25분 (최적화) | 1.2GB | 34.6% |
    | 토큰화 | 1.6GB | 45분 | 2.5GB | 67.7% |
    | N-gram 생성 | 5.3GB (71M) | 30분 | 4.5GB | - |
    | 빈도 필터링 | 15MB (0.67M) | 5분 | 256MB | 99.0% |

- **소스별 정제 특징**

    | 소스 | 특수 패턴 | 평균 길이 | 정제율 | 특징 |
    |------|----------|-----------|--------|------|
    | 연합뉴스 | `(서울=연합뉴스)` | 1,523→892자 | 41.5% | 가장 엄격 |
    | 이데일리 | `[이데일리 기자]` | 1,287→781자 | 39.3% | 관련기사 링크 |
    | 인포맥스 | `(연합인포맥스)` | 1,094→698자 | 36.2% | 표/그래프 많음 |
    | MPB | 섹션 구분 유지 | 8,234→6,998자 | 15.0% | 형식 보존 중요 |
    | 채권 | HTML 태그 | 2,156→1,425자 | 33.9% | 숫자 많음 |

- **eKoNLPy 금융 특화 기능**

    ```python
    # 금융 복합명사 인식
    '콜금리' → 단일 토큰 (일반 형태소 분석기: '콜' + '금리')
    'CD금리', 'RP매매', 'FOMC' → 보존

    # 금액 정규화
    '3조5천억원' → '3.5조원'
    '2,500억' → '2500억'

    # 경제 약어 사전
    {'한은': '한국은행', 'ECB': '유럽중앙은행', '연준': '미국연방준비제도'}
    ```

---

### 5페이지 — N-gram 특징 추출 및 감성 분석

- **N-gram 생성 측정값(좌)**
    
    초기 생성: **71,163,146개** 고유 n-gram

    빈도 필터(≥15): **670,616개** (99.0% 제거)
    
    최종 vocabulary: **15MB**
    
- **NGram 클래스 구현(우 상단)**
    ```python
    # ngram_dohy.py 실제 구현
    class NGram:
        def str_to_list(self, tokens_str):
            return ast.literal_eval(tokens_str)  # 안전한 문자열 파싱
        def remove_pos(self, tokens, pos_tags=['NNG','VA','MAG','VV','VCN']):
            return [token for token, pos in tokens if pos in pos_tags]
        def ngramize(self, filtered_tokens, n):
            return [' '.join(filtered_tokens[i:i+n]) for i in range(len(filtered_tokens)-n+1)]
    ```
    
- **메모리 효율 최적화(우 중단)**
    ```python
    # ngram_counter.py chunk 처리
    def count_ngrams_in_file(file_path, chunk_size=100000):
        ngram_counter = Counter()
        chunk = []
        # 10만개 단위로 Counter 업데이트
        if len(chunk) >= chunk_size:
            ngram_counter.update(chunk)
            chunk = []
    ```
    
- **빈도 분포 분석(우 하단)**
    
    | 빈도 범위 | N-gram 수 | 누적 비율 | 메모리 |
    |-----------|-----------|-----------|---------|
    | 1-14회 | 70,492,530 | 99.0% | 제외 |
    | 15-99회 | 579,284 | 99.8% | 포함 |
    | 100+회 | 91,332 | 100% | 포함 |
    
    **필터 조건**: `if count >= min_frequency` (min_frequency=15)
    
- **확률 계산 최적화**
    ```python
    # 로그 확률로 언더플로우 방지
    log_prob_0 = np.log(23132980/55894039) = -0.8825
    log_prob_1 = np.log(32761059/55894039) = -0.5342
    ```

---

### 6페이지 — 최종 결과 & 성능 분석

- **최종 성능 카드(좌 상단)**

    **문장 단위 NBC (논문 방법론)**
    **F1-Score 71.47%** / Accuracy 67.79%

    Precision 70.22% / Recall 72.77%

    샘플 수: 2,823,248 문장 (날짜 단위 대비 2,008배↑)
    
- **혼동 행렬 상세 분석(좌 중단)**
    
    | 실제\예측 | Dovish | Hawkish | 정확도 |
    |-----------|---------|----------|--------|
    | Dovish(83) | TN: 67 | FP: 16 | 80.7% |
    | Hawkish(83) | FN: 16 | TP: 67 | 80.7% |
    
    Hawkish 재현율이 높은 이유: 클래스 불균형(58.6%)
    
- **시계열 예측 패턴(좌 하단)**
    
    주요 전환점 포착률: 68% (17/25 전환점)
    
    · 2022.07 긴축 시작: ✓ 포착
    
    · 2023.01 긴축 지속: ✓ 포착
    
    · 2024.08 피벗 신호: ✗ 미포착 (시계열 미고려)
    
- **성능 개선 과정(우 상단)**
    
    | 시도 | 변경사항 | F1-Score | 개선 |
    |------|----------|----------|------|
    | v1 | 단순 BoW | 45.2% | - |
    | v2 | +2-gram | 58.3% | +13.1%p |
    | v3 | +3-5gram | 62.1% | +3.8%p |
    | v4 | 빈도≥15 필터 | 65.48% | +3.38%p |
    | v5 | 문장 단위 학습 | 71.47% | +5.99%p |
    
- **실패 사례 분석(우 중단)**
    
    **2024년 피벗 미포착 원인**
    
    · NBC의 시계열 정보 무시
    
    · "선제적", "예방적" 같은 미묘한 표현 해석 실패
    
    · 훈련 데이터의 피벗 사례 부족 (대부분 일방향 변화)
    
- **핵심 인사이트(우 하단)**
    
    **성공 요인**
    
    · 99% 노이즈 제거로 정밀도 향상
    
    · Market Approach로 객관적 라벨링
    
    · 대규모 데이터(359K)로 robust 학습
    
    **개선 필요**
    
    · 시계열 패턴 학습 (LSTM 도입)
    
    · 문맥 이해 강화 (BERT fine-tuning)
    
    · 클래스 균형 조정 (SMOTE, cost-sensitive)
    
    **목표**: 논문 수준 80% 정확도 달성

---

### 7페이지 — 기술 스택 & 참고 문헌

- **파이프라인별 스택**

    **1. 데이터 수집**
    · 라이브러리: Scrapy 2.11, BeautifulSoup4, Requests
    · 채권 크롤링: ThreadPoolExecutor (max_workers=5)
    · 뉴스 크롤링: 소스별 순차 처리
    · API: 연합뉴스 API v2 (2016년 이후)

    **2. 데이터 전처리**
    · 핵심 라이브러리: pandas, numpy, regex
    · NLP: eKoNLPy 0.97+, Mecab
    · DB: PostgreSQL (psycopg2-binary 2.9.0)

    **3. 특징 추출**
    · N-gram 생성: ast.literal_eval, Counter
    · 토큰화 최적화: 효율적인 메모리 사용
    · 메모리 관리: chunk 처리 (100,000개 단위)

    **4. 모델링**
    · 베이스라인: NBC (scikit-learn 1.0.0+)
    · 스무딩: Laplace (α=1)
    · 분할: train_test_split (90:10, random_state=33)

    **5. 평가·시각화**
    · 평가지표: F1-Score, Precision, Recall
    · 시각화: matplotlib, seaborn, WordCloud
    · 생성된 시각화:
      - visualizations/sentence_nbc_performance.png: 문장 NBC 성능 (F1 71.47%)
      - visualizations/data_pipeline.png: 데이터 처리 파이프라인
      - visualizations/label_distribution.png: 라벨 분포 (44.6% vs 55.4%)
      - visualizations/ngram_wordcloud.png: N-gram 워드클라우드
      - visualizations/confusion_matrix.png: 혼동행렬

- **개발 및 운영 환경**

    **환경/도구**
    · Python 3.12, conda/venv, pip
    · Jupyter, pytest, logging, tqdm
    · 성능: 멀티프로세싱 (n_jobs=8)

    **재현성**
    · random seed 고정 (random_state=33)
    · requirements.txt (48개 패키지 버전 고정)
    · 설정 분리: .env (환경변수), config 파일

    **데이터 소스(I/O)**
    · 입력: 뉴스(HTML/JSON), MPB(PDF), 금리(CSV)
    · 중간: PostgreSQL JSONB (9개 테이블 80개 필드)
    · 산출: N-grams(JSON), NBC모델(PKL),
             결과(CSV), 시각화(PNG), 리포트(MD)

- **참고 문헌**

    **Park et al. (BOK Working Paper No. 2019-1, 2020)**
    "Deciphering Monetary Policy Board Minutes Through Text Mining Approach: The Case of South Korea"

    · NBC accuracy 80% 벤치마크, N-gram(1-5) 방법론 검증
    · 적용 포인트: Market Approach 라벨링 설계, 빈도 필터링(>15) 기준,
                  라플라스 스무딩 파라미터(α=1) 선택 근거

    **GitHub Repository**
    github.com/sesac-analyst/BOK_TEAM_1

---

### 프로젝트 핵심 성과

**데이터 처리**
- 359,151개 금융 뉴스 수집 (99.8% 수집률)
- 2.82M 문장 분리 및 처리
- 71.2M → 0.67M n-gram 필터링 (99% 노이즈 제거)

**모델링 성과**
- 문장 단위 NBC: F1-Score 71.47% 달성
- 30회 배깅으로 안정적 성능 확보
- 날짜 단위 과적합 문제 해결 (F1 100% → 71.47%)

**기술적 성취**
- 논문 방법론 재현 및 개선
- PostgreSQL JSONB 기반 대규모 데이터 처리
- 멀티프로세싱으로 처리 시간 75% 단축

**핵심 발견**
- Out-of-domain 평가의 중요성 확인
- 문장 단위 처리가 날짜 단위보다 효과적
- 샘플 수 증가 (1,405 → 2.82M)로 과적합 해결

---

*최종 업데이트: 2025-09-22*