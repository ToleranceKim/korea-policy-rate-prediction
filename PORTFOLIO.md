# 한국은행 기준금리 예측 프로젝트 포트폴리오

### 1페이지 — 금융 텍스트 마이닝 기반 기준금리 방향성 예측 〔히어로 페이지〕

- **Overview**
    
    · 359,151개 금융 뉴스와 224개 MPB 의사록을 분석하여 한국은행 기준금리 방향성(Dovish/Hawkish) 예측
    
    · 53.4M개 n-gram에서 1.58M개 핵심 특징 추출(97% 노이즈 제거)로 메모리 48.1MB 최적화
    
- **Background**
    
    · 텍스트 데이터를 활용한 통화정책 예측의 필요성 증대
    
    · "Deciphering Monetary Policy Board Minutes Through Text Mining" 논문 재현 및 한국 시장 적용
    
- **담당역할 (모델링 제외 전체)**

    · **데이터 수집**: 359,151개 뉴스 크롤링 파이프라인 구축
      - Scrapy 기반 UnifiedNewsCrawler 설계 및 구현
      - Edaily preview 버그 수정으로 완전 본문 수집 달성
      - InfoMax 3,000자 제한 해제, 연합뉴스 API 통합
      - bond_parallel_crawler.py 병렬 처리 (ThreadPoolExecutor)

    · **데이터 전처리**: prepare_paper_dataset.py 구현
      - 85개 필드 스키마 설계 (tokenized_content, pos_tags, sentiment scores)
      - PostgreSQL JSONB 저장 구조 설계
      - db_insert_dohy.py 배치 삽입 최적화 (page_size=1000)
      - bond_cleansing.py 정규표현식 정제 파이프라인

    · **특징 추출**: ngram_dohy.py 구현
      - 53.4M → 1.58M n-grams 필터링 (빈도>5, 97% 노이즈 제거)
      - Counter 기반 chunk 처리로 메모리 48.1MB 최적화
      - eKoNLPy 품사 필터링 (NNG, VA, MAG, VV, VCN)

    · **라벨링**: 콜금리 변동 기반 Market-based Approach
      - 41개 고유 금리 변동점 (중복 제거 후, 2008-2025)
      - 2개월 후 실제 금리 변화 기반 (±0.01%p 임계값)
      - 122,315개 기사 → 1,852,138개 문장 라벨 확장
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
      - Train/Test split (80:20, random_state=33)

    · **성능 평가**:
      - 문장 단위 NBC (성공): F1-Score 79.3% 달성 (1,852,138개 문장, 30회 배깅)
      - 날짜 단위 NBC (과적합): F1-Score 100% (1,405 날짜)
      - Precision 76.7%, Recall 82.1%, Accuracy 77.4%

    · **모델 성능 시각화**: nbc_modeling.ipynb
      - confusion_matrix.png: 혼동행렬 히트맵
      - label_ratio.png: Dovish/Hawkish 클래스 비율
      - result_scores.png: 시계열 예측 성능 그래프
      - performance_curve.png: v1→v4 단계별 성능 개선 곡선
      - class_distribution.png: Train/Test 클래스 분포
    
- **파이프라인**

    **① 데이터 수집 (359K 뉴스)**
    · 뉴스: 359,151건 (인포맥스 177K, 이데일리 112K, 연합 69K)
    · MPB 의사록: 224건 PDF → PyPDF2 추출
    · 금리 데이터: 콜금리 일별, 기준금리 41개 고유 변동점 (중복 검증 후)
    · PostgreSQL JSONB 저장 (85개 필드 스키마)

    **② 토큰화 (eKoNLPy)**
    · eKoNLPy 0.97+ Mecab 기반 형태소 분석
    · 품사 태깅 및 필터링 (NNG, VA, MAG, VV, VCN)
    · 정규표현식 클렌징: HTML태그, 특수문자 제거
    · 배치 처리: 1,000건 단위 메모리 효율화

    **③ N-gram 생성 (53.4M→1.58M)**
    · 1-5gram 추출: 53,371,110개 초기 생성
    · 빈도 필터링(>5): 1,577,569개 (97% 노이즈 제거)
    · Counter 기반 메모리 최적화 → 48.1MB1. 데이터 수집: Scrapy 2.11, BeautifulSoup4, ThreadPoolExecutor

2. 데이터 전처리: pandas, regex, eKoNLPy 0.97+, PostgreSQL

3. 특징 추출: Counter, multiprocessing.Pool (8 cores)

4. 모델링: scikit-learn 1.0.0+ (NBC), Laplace (α=1)

5. 평가·시각화: matplotlib, seaborn, WordCloud

    **④ NBC 모델링 (Laplace α=1)**
    · Market Approach 라벨링 (Dovish/Hawkish)
    · 라플라스 스무딩 적용 (α=1)
    · Train/Test split: 1,015/254 (80:20, random_state=33)

    **⑤ 성능 평가 (F1 79.3%)**
    · Accuracy 77.4%, Precision 76.7%, Recall 82.1%
    · 혼동행렬: 1.85M 문장 학습 (날짜 단위 대비 1,317배↑)
    · 라벨 분포: Dovish 47.3% vs Hawkish 52.7% (균형적)
    · 시각화: 5개 차트 생성 (visualizations/)
    
- **KPI 카드**
    - **데이터 처리**
        
        뉴스 수집률: 359,151/360,000 = 99.8%, 노이즈 제거: 97.0%
        
    - **모델 성능**

        **F1-Score 79.3%** (Precision 76.7%, Recall 82.1%)
        
    - **시스템 효율**
        
        처리 시간 **75% 감소** (4h→1h), 메모리 **48.1MB** 최적화
        

---

### 2페이지 — 데이터 수집 및 크롤링 아키텍처

- **수집 규모**: 총 **359,151개** 뉴스 기사 (2014.01-2025.09, 144개월)
    - 인포맥스: 177,406개 (49.4%)
    - 이데일리: 112,201개 (31.2%)  
    - 연합뉴스: 69,544개 (19.4%)
    - 평균 기사 길이: **1,368자** (content_stats 검증)
- **크롤링 최적화**
    - **Edaily 버그 수정**: `extract_edaily_article()` 메서드 추가로 preview(300자) → 전체 본문 수집
    - **InfoMax 제한 해제**: `content[:3000]` 제거로 전체 기사 수집 가능
    - **연합뉴스 API 통합**: 2016년 이후 공식 API(`ars.yna.co.kr/api/v2`), 이전 데이터는 네이버 아카이브 활용
- **병렬 처리 아키텍처**
    ```python
    ThreadPoolExecutor(max_workers=5)  # bond_parallel_crawler.py 실제 설정
    fetch_url_with_retries(url, max_retries=3, delay=2)  # 재시도 메커니즘
    time.sleep(0.3)  # API 호출 간격 제어
    ```
- **수집 성과 표**
    
    | 연도 | 기사 수 | 일평균 | 주요 이슈 |
    |------|---------|---------|----------|
    | 2022 | 42,696 | 117개 | 급격한 금리 인상 |
    | 2023 | 40,494 | 111개 | 긴축 지속 |
    | 2024 | 40,117 | 110개 | 피벗 논의 |
    
- **MPB 의사록**: 224개 PDF → PyPDF2로 '토의내용', '심의결과' 섹션 자동 추출
- **데이터베이스**: PostgreSQL JSONB 활용, `psycopg2.extras.execute_values` (page_size=1000)

---

### 3페이지 — 베이스라인 모델 설계와 한계 파악

- **모델 진화 과정**
    
    | 단계 | 접근법 | 구현 상태 | 성능 | 핵심 변경사항 |
    |------|--------|-----------|------|-------------|
    | v0 | Lexical (Seed words) | 미구현 | - | 논문 방법론 |
    | v1 | Market Approach (날짜) | 과적합 | F1 100% | 1,405 날짜 |
    | v1.5 | Market Approach (문장) | 성공 | F1 79.3% | 1.85M 문장 |
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
    
    날짜 단위: F1 100% (과적합) → 문장 단위: F1 79.3% (정상화)

    30회 배깅 앙상블로 안정적 성능 확보
    
- **한계 분석**
    
    · 단어 독립 가정: "금리" "인상" 분리 → "금리 인상" 맥락 손실
    
    · 시계열 미고려: 2024년 피벗 신호 포착 실패 (전환점 정확도 68%)
    
    · Hawkish 과대 예측: 151 vs 103 (클래스 불균형 영향)

---

### 4페이지 — 텍스트 전처리 및 토큰화 프로세스

- **전처리 파이프라인 측정값(좌)**
    
    Raw: 359,151개 문서 (13GB) → Clean: 358,923개 (99.94%)
    
    처리 시간: 단일 스레드 4시간 → **multiprocessing.Pool(8) 1시간**
    
- **데이터 정제 상세(우 상단)**
    ```python
    # bond_cleansing.py 실제 정규표현식 패턴
    re.sub('<.*?>', '', text)  # HTML 태그 제거
    re.sub('([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', '', text)  # 이메일
    re.sub('([ㄱ-ㅎㅏ-ㅣ]+)', '', text)  # 한글 자모
    re.sub('[^a-zA-Z0-9ㄱ-ㅣ가-힣]', ' ', text)  # 특수문자
    re.sub('\d{6}', '', text)  # 종목코드 제거
    ```
    
    중복 제거: 228개 기사 (0.06%) 제거
    
- **eKoNLPy 토큰화 성능(우 중단)**
    ```python
    # tokenization.ipynb 배치 처리 최적화
    def process_in_batches(df, batch_size=1000):
        # 1000개 단위 처리로 메모리 효율 60% 개선
        batch.to_csv(f'processed_batch_{start}.csv')  # 중간 결과 저장
    ```
    
    품사 필터링: NNG(명사), VA(형용사), MAG(부사), VV(동사), VCN(부정지정사)
    
    **pykospacing**: 한국어 띄어쓰기 교정 추가 (requirements.txt)
    
- **데이터 통합 결과(우 하단)**

    MPB discussion + decision → content: 224개 문서

    날짜 매칭: 1,269개 거래일 × 평균 283개 기사/일

    **메모리 최적화**: 13GB → 2.8GB (78.5% 감소)

    **PostgreSQL 저장**: db_insert_dohy.py로 배치 삽입

    **시각화**: data_size_comparison.png로 처리 단계별 데이터 감소 확인

---

### 5페이지 — N-gram 특징 추출 및 감성 분석

- **N-gram 생성 측정값(좌)**
    
    초기 생성: **53,371,110개** 고유 n-gram
    
    빈도 필터(>5): **1,577,569개** (97.0% 제거)
    
    최종 DataFrame: **48.1MB** 메모리
    
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
    | 1-5회 | 51,793,541 | 97.0% | 제외 |
    | 6-99회 | 1,486,237 | 99.8% | 포함 |
    | 100+회 | 91,332 | 100% | 포함 |
    
    **필터 조건**: `if count > min_frequency` (min_frequency=5)
    
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
    **F1-Score 79.3%** / Accuracy 77.4%

    Precision 76.7% / Recall 82.1%

    샘플 수: 1,852,138 문장 (날짜 단위 대비 1,317배↑)
    
- **혼동 행렬 상세 분석(좌 중단)**
    
    | 실제\예측 | Dovish | Hawkish | 정확도 |
    |-----------|---------|----------|--------|
    | Dovish(124) | TN: 65 | FP: 59 | 52.4% |
    | Hawkish(130) | FN: 38 | TP: 92 | 70.8% |
    
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
    | v4 | 빈도>5 필터 | 65.48% | +3.38%p |
    | v5 | 문장 단위 학습 | 79.3% | +13.82%p |
    
- **실패 사례 분석(우 중단)**
    
    **2024년 피벗 미포착 원인**
    
    · NBC의 시계열 정보 무시
    
    · "선제적", "예방적" 같은 미묘한 표현 해석 실패
    
    · 훈련 데이터의 피벗 사례 부족 (대부분 일방향 변화)
    
- **핵심 인사이트(우 하단)**
    
    **성공 요인**
    
    · 97% 노이즈 제거로 정밀도 향상
    
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
    · 병렬처리: ThreadPoolExecutor (max_workers=5)
    · API: 연합뉴스 API v2 (2016년 이후)

    **2. 데이터 전처리**
    · 핵심 라이브러리: pandas, numpy, regex
    · NLP: eKoNLPy 0.97+, Mecab, pykospacing
    · DB: PostgreSQL (psycopg2-binary 2.9.0)

    **3. 특징 추출**
    · N-gram 생성: ast.literal_eval, Counter
    · 병렬화: multiprocessing.Pool (8 cores)
    · 메모리 관리: chunk 처리 (100,000개 단위)

    **4. 모델링**
    · 베이스라인: NBC (scikit-learn 1.0.0+)
    · 스무딩: Laplace (α=1)
    · 분할: train_test_split (80:20, random_state=33)

    **5. 평가·시각화**
    · 평가지표: F1-Score, Precision, Recall
    · 시각화: matplotlib, seaborn, WordCloud
    · 생성된 시각화:
      - visualizations/sentence_nbc_performance.png: 문장 NBC 성능 (F1 79.3%)
      - visualizations/data_pipeline.png: 데이터 처리 파이프라인
      - visualizations/label_distribution.png: 라벨 분포 (47.3% vs 52.7%)
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
    · 중간: PostgreSQL JSONB (85개 필드)
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
- 1.85M 문장 분리 및 처리
- 53.4M → 1.58M n-gram 필터링 (97% 노이즈 제거)

**모델링 성과**
- 문장 단위 NBC: F1-Score 79.3% 달성
- 30회 배깅으로 안정적 성능 확보
- 날짜 단위 과적합 문제 해결 (F1 100% → 79.3%)

**기술적 성취**
- 논문 방법론 재현 및 개선
- PostgreSQL JSONB 기반 대규모 데이터 처리
- 멀티프로세싱으로 처리 시간 75% 단축

**핵심 발견**
- Out-of-domain 평가의 중요성 확인
- 문장 단위 처리가 날짜 단위보다 효과적
- 샘플 수 증가 (1,405 → 1.85M)로 과적합 해결

---

*최종 업데이트: 2025-09-22*