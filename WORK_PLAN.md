# 논문 재현 작업 계획서 (FAST TRACK)
## "Deciphering Monetary Policy Board Minutes Through Text Mining Approach" 재현

### 📋 프로젝트 개요
- **목표**: 한국은행 통화정책방향 예측을 위한 텍스트 마이닝 연구 재현
- **데이터 기간**: 2014년 1월 - 2025년 12월 (12년간)
- **현재 상태**: 뉴스 데이터 수집 완료 (144개월 분)

---

## 🎯 Phase 1: 데이터 수집 완료 및 검증 (3일)

### 1.1 뉴스 데이터 (✅ 완료)
- [x] 2014-2025년 전체 뉴스 수집 완료 (144개월)
- [x] 연합뉴스 (2016-2025), 이데일리, 인포맥스 (2014-2025)
- [ ] **즉시**: 데이터 품질 검증 스크립트 실행
- [ ] **즉시**: 중복 제거 및 통계 생성

### 1.2 MPB 의사록 수집 (Day 1)
- [x] MPB 크롤러 구현 완료
- [ ] **오늘**: 2014-2025년 의사록 수집 실행 (~200개)
- [ ] PDF 텍스트 추출 검증

### 1.3 시장 데이터 수집 (Day 1)
- [x] 콜금리/기준금리 크롤러 구현
- [ ] **오늘**: 2014-2025년 일별 데이터 수집
- [ ] 시계열 정합성 검증

### 1.4 채권 리포트 수집 (Day 2-3)
- [x] 네이버 금융 크롤러 구현
- [ ] 2014-2025년 리포트 수집 (병렬 처리)
- [ ] PDF 텍스트 추출

---

## 🔧 Phase 2: 텍스트 전처리 (3일)

### 2.1 eKoNLPy 설정 및 최적화
```python
# 필요 구현 사항
- [ ] eKoNLPy 설치 및 금융 사전 구성
- [ ] 토큰화 함수 구현
- [ ] POS 태깅 및 필터링 (NNG, VA, MAG, VV, VCN)
- [ ] 성능 최적화 (병렬 처리)
```

### 2.2 N-gram 생성
```python
# ngram_dohy.py 구현
- [ ] 1-gram 추출 (unigrams)
- [ ] 2-gram 추출 (bigrams)
- [ ] 3-gram 추출 (trigrams)  
- [ ] 4-gram 추출 (fourgrams)
- [ ] 5-gram 추출 (fivegrams)
- [ ] 빈도수 계산 및 필터링
```

### 2.3 문서 전처리 파이프라인
- [ ] MPB 의사록 전처리 모듈
- [ ] 뉴스 기사 전처리 모듈
- [ ] 채권 리포트 전처리 모듈
- [ ] 통합 전처리 파이프라인 구축

---

## 📊 Phase 3: 감성 사전 구축 (5일)

### 3.1 Market Approach (시장 기반)
```python
# 콜금리 변동 기반 레이블링
- [ ] 콜금리 변동 임계값 설정 (상승/하락/유지)
- [ ] MPB 의사록-콜금리 매칭
- [ ] 시장 기반 훈련 데이터 생성
- [ ] NBC 모델 학습 (n-gram 특징)
```

### 3.2 Lexical Approach (어휘 기반)
```python
# Seed Words + SentProp
- [ ] Hawkish seed words 선정 (긴축적)
- [ ] Dovish seed words 선정 (완화적)
- [ ] SentProp 알고리즘 구현
- [ ] 감성 사전 확장 (PMI 기반)
- [ ] 도메인 특화 감성 사전 구축
```

### 3.3 감성 점수 계산
- [ ] 문서별 hawkish/dovish 점수 계산
- [ ] 가중치 적용 (TF-IDF, 위치 가중치)
- [ ] 정규화 및 스케일링
- [ ] 검증 메트릭 구현

---

## 🤖 Phase 4: 모델링 및 실험 (5일)

### 4.1 Naive Bayes Classifier
```python
# NBC 구현 및 학습
- [ ] 특징 벡터 생성 (n-gram 기반)
- [ ] 모델 학습 (Market/Lexical approach)
- [ ] 하이퍼파라미터 튜닝
- [ ] 교차 검증 (10-fold CV)
```

### 4.2 감성 지표 생성
- [ ] MPB Tone 지표 계산
- [ ] MPB Uncertainty 지표 계산
- [ ] 시계열 지표 구성
- [ ] 지표 검증 및 시각화

### 4.3 Taylor Rule 증강
```python
# Augmented Taylor Rule
- [ ] 기본 Taylor Rule 구현
- [ ] 텍스트 지표 통합
- [ ] 회귀 분석 수행
- [ ] R² 개선 검증 (0.095 → 0.446)
```

---

## 📈 Phase 5: 평가 및 검증 (3일)

### 5.1 성능 평가
- [ ] 정확도, 정밀도, 재현율 계산
- [ ] F1-score 및 AUC-ROC
- [ ] 혼동 행렬 분석
- [ ] 접근법별 성능 비교 (Market vs Lexical)

### 5.2 결과 재현성 검증
- [ ] 논문 Table 1 재현 (기초 통계)
- [ ] 논문 Table 2 재현 (n-gram 빈도)
- [ ] 논문 Table 3 재현 (감성 분류 성능)
- [ ] 논문 Table 4 재현 (Taylor Rule 결과)

### 5.3 시각화 및 분석
- [ ] Word Cloud 생성 (Hawkish/Dovish)
- [ ] 시계열 감성 추이 그래프
- [ ] 정책 결정과 감성 지표 상관관계
- [ ] 예측 오류 분석

---

## 🚀 Phase 6: 확장 및 개선 (선택적)

### 6.1 최신 데이터 적용
- [ ] 2018-2025년 데이터로 모델 확장
- [ ] COVID-19 기간 특수성 분석
- [ ] 최근 금리 인상기 예측 성능

### 6.2 모델 개선
- [ ] Deep Learning 모델 적용 (BERT, KoBERT)
- [ ] Ensemble 방법론 적용
- [ ] 실시간 예측 시스템 구축

### 6.3 추가 분석
- [ ] 증권사별 감성 차이 분석
- [ ] 언론사별 논조 비교
- [ ] 주제별 감성 분석 (LDA + Sentiment)

---

## 📁 디렉토리 구조

```
mpb-stance-mining/
├── data/
│   ├── raw/                 # 원본 수집 데이터
│   │   ├── mpb/             # MPB 의사록
│   │   ├── news/            # 뉴스 기사
│   │   ├── bond/            # 채권 리포트
│   │   └── market/          # 시장 데이터
│   ├── processed/           # 전처리된 데이터
│   │   ├── tokenized/       # 토큰화 결과
│   │   ├── ngrams/          # N-gram 데이터
│   │   └── features/        # 특징 벡터
│   └── results/            # 실험 결과
│       ├── models/         # 학습된 모델
│       ├── predictions/    # 예측 결과
│       └── evaluation/     # 평가 메트릭
├── preprocess/
│   ├── tokenizer.py        # eKoNLPy 토큰화
│   ├── ngram_generator.py  # N-gram 생성
│   └── pipeline.py         # 전처리 파이프라인
├── modeling/
│   ├── nbc/                # Naive Bayes
│   ├── sentiment/          # 감성 분석
│   └── taylor_rule/        # Taylor Rule
├── analysis/
│   ├── visualization.py    # 시각화
│   └── evaluation.py       # 평가 메트릭
└── scripts/
    ├── run_preprocessing.py # 전처리 실행
    ├── run_training.py      # 모델 학습
    └── run_evaluation.py    # 평가 실행
```

---

## 🔍 핵심 구현 체크리스트

### 필수 구현 사항
- [ ] eKoNLPy 기반 한국어 금융 텍스트 전처리
- [ ] 1-5 gram 추출 및 빈도 분석
- [ ] Market Approach 감성 분류기
- [ ] Lexical Approach (SentProp) 감성 사전
- [ ] NBC 모델 학습 및 평가
- [ ] Taylor Rule 증강 실험

### 검증 사항
- [ ] 뉴스 데이터 품질 (2014-2025년 144개월)
- [ ] MPB 의사록 (~200개)
- [ ] 감성 분류 정확도 80% 이상
- [ ] Taylor Rule R² 개선 확인

---

## 📅 Fast Track 일정 (총 19일)

| 일정 | 작업 내용 | 완료 기준 |
|------|-----------|-----------|
| Day 1-3 | 데이터 수집 완료 | MPB/시장 데이터 수집 |
| Day 4-6 | 텍스트 전처리 | eKoNLPy 적용, N-gram 추출 |
| Day 7-11 | 감성 사전 구축 | Market/Lexical approach |
| Day 12-16 | 모델링 | NBC 학습, Taylor Rule |
| Day 17-19 | 평가 및 검증 | 성능 측정, 결과 비교 |

---

## 🛠 기술 스택

### 필수 라이브러리
```python
# 텍스트 처리
ekonlpy==1.0.4          # 한국어 금융 텍스트 분석
pykospacing==0.5        # 한국어 띄어쓰기

# 머신러닝
scikit-learn==1.3.0     # NBC, 평가 메트릭
numpy==1.24.3           # 수치 연산
pandas==2.0.3           # 데이터 처리

# 크롤링
scrapy==2.11.0          # 웹 크롤링
beautifulsoup4==4.12.2  # HTML 파싱
PyPDF2==3.0.1           # PDF 처리

# 시각화
matplotlib==3.7.2       # 그래프
wordcloud==1.9.2        # 워드클라우드
seaborn==0.12.2         # 통계 시각화
```

---

## 📝 참고 사항

1. **데이터 수집 현황**
   - ✅ 뉴스: 2014-2025년 완료 (144개월)
   - ⏳ MPB 의사록: 즉시 수집 시작
   - ⏳ 콜금리: 즉시 수집 시작
   - ⏳ 채권 리포트: Day 2-3

2. **전처리 핵심**
   - eKoNLPy 금융 사전 커스터마이징 필수
   - POS 필터링: NNG, VA, MAG, VV, VCN만 사용

3. **실험 재현성**
   - Random seed 고정 (42)
   - 10-fold cross validation 필수
   - 모든 하이퍼파라미터 문서화

4. **성능 목표**
   - 감성 분류 정확도: 80% 이상
   - Taylor Rule R²: 0.4 이상
   - 처리 속도: 10만 문서/시간

---

## 🎓 예상 학습 내용

- 한국어 금융 텍스트 특성 이해
- N-gram 기반 특징 추출 기법
- 감성 사전 구축 방법론 (Market vs Lexical)
- NBC를 활용한 텍스트 분류
- 경제 모델(Taylor Rule)과 텍스트 분석 통합
- 대규모 텍스트 데이터 처리 최적화

---

이 계획서를 기반으로 단계별로 작업을 진행하며, 각 단계마다 검증과 피드백을 통해 품질을 확보합니다.