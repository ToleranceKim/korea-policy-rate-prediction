# 시각화 개발 계획서

## 📋 프로젝트 개요

### 목적
한국은행 기준금리 예측 프로젝트의 데이터 분석 결과와 모델 성능을 효과적으로 시각화하여 포트폴리오의 설득력과 가독성을 향상

### 범위
- 기존 시각화 자료 정리 및 활용
- 누락된 연결 코드 개발
- 새로운 시각화 생성
- 포트폴리오 문서 통합

---

## 🎯 시각화 목표

### 1. 즉시 사용 가능한 시각화 (기존 파일)
- [x] `confusion_matrix.png` - 혼동행렬 히트맵
- [x] `label_ratio.png` - Dovish/Hawkish 클래스 비율
- [x] `result_scores.png` - 시계열 예측 성능
- [x] `topic_MULTI.png` - MPB 워드클라우드
- [x] `News.png` - 뉴스 분포

### 2. 개발 필요 시각화
- [ ] N-gram Top 20 막대그래프
- [ ] 성능 개선 곡선 (v1→v4)
- [ ] 월별 뉴스 수집량 추이
- [ ] 언론사별 비율 파이차트
- [ ] 전처리 전후 데이터 크기 비교

---

## 🔧 기술 구현 계획

### Phase 1: 데이터 준비 (2시간)

#### 1.1 누락 파일 생성
```python
# create_model_data.py
def create_date_ngram_json():
    """
    PostgreSQL에서 날짜별 n-gram 데이터 추출
    Input: PostgreSQL connection
    Output: date_ngram.json
    """
    pass

def create_date_label_json():
    """
    콜금리 변동 기반 일별 라벨 생성
    Input: call_rates_2014_2025.csv
    Output: date_label.json
    """
    pass
```

#### 1.2 필요 데이터 구조
```json
// date_ngram.json
{
    "2014-01-02": ["금리", "인상", "경제", ...],
    "2014-01-03": ["통화", "정책", "완화", ...],
    ...
}

// date_label.json
{
    "2014-01-02": 0,  // Dovish
    "2014-01-03": 1,  // Hawkish
    ...
}
```

### Phase 2: 시각화 코드 구현 (1시간)

#### 2.1 N-gram 분석 시각화
```python
# visualization_generator.py
def plot_top20_ngrams(df):
    """
    상위 20개 N-gram 빈도 막대그래프
    """
    top20 = df.nlargest(20, 'sum')
    plt.figure(figsize=(10, 8))
    plt.barh(range(len(top20)), top20['sum'].values)
    plt.yticks(range(len(top20)), top20.index)
    plt.xlabel('빈도수')
    plt.title('Top 20 N-grams by Frequency')
    plt.tight_layout()
    plt.savefig('visualizations/top20_ngrams.png')
```

#### 2.2 성능 개선 시각화
```python
def plot_performance_curve():
    """
    v1 → v4 성능 개선 곡선
    """
    versions = ['v1', 'v2', 'v3', 'v4']
    f1_scores = [45.2, 58.3, 62.1, 65.48]

    plt.figure(figsize=(8, 6))
    plt.plot(versions, f1_scores, marker='o', linewidth=2)
    plt.xlabel('Version')
    plt.ylabel('F1-Score (%)')
    plt.title('Model Performance Improvement')
    plt.grid(True, alpha=0.3)
    plt.savefig('visualizations/performance_curve.png')
```

#### 2.3 데이터 수집 통계
```python
def plot_news_statistics():
    """
    월별 수집량 및 언론사별 비율
    """
    # 월별 수집량
    dates = pd.date_range('2014-01', '2025-09', freq='M')
    # 실제 데이터로 교체 필요

    # 언론사별 비율
    sources = {'인포맥스': 177406, '이데일리': 112201, '연합뉴스': 69544}
    plt.pie(sources.values(), labels=sources.keys(), autopct='%1.1f%%')
    plt.savefig('visualizations/news_sources.png')
```

### Phase 3: 테스트 및 검증 (30분)

#### 3.1 체크리스트
- [ ] 모든 시각화 파일 생성 확인
- [ ] 이미지 품질 검증 (해상도, 레이블)
- [ ] 파일 크기 최적화
- [ ] 색상 일관성 확인

#### 3.2 출력 디렉토리 구조
```
visualizations/
├── existing/           # 기존 시각화
│   ├── confusion_matrix.png
│   ├── label_ratio.png
│   └── result_scores.png
├── generated/          # 새로 생성
│   ├── top20_ngrams.png
│   ├── performance_curve.png
│   ├── news_timeline.png
│   └── news_sources.png
└── README.md          # 시각화 설명서
```

---

## 📊 포트폴리오 통합 계획

### 통합 위치 및 설명

| 시각화 | 포트폴리오 위치 | 설명 |
|--------|----------------|------|
| 월별 수집량 | 2페이지 - 데이터 수집 | 359K 뉴스의 시계열 분포 |
| 언론사 비율 | 2페이지 - 데이터 수집 | 3개 언론사 균형 |
| N-gram Top 20 | 5페이지 - N-gram 특징 | 핵심 특징 추출 효과 |
| 성능 곡선 | 6페이지 - 성능 분석 | 단계별 개선 과정 |
| 혼동행렬 | 6페이지 - 성능 분석 | 분류 성능 상세 |

---

## ⚠️ 리스크 및 대응

### 잠재 이슈
1. **데이터 누락**: date_ngram.json 생성 실패
   - 대응: 샘플 데이터로 시각화 테스트

2. **메모리 부족**: 53M n-gram 처리
   - 대응: chunk 단위 처리 (이미 구현됨)

3. **실행 시간**: 전체 파이프라인 48시간+
   - 대응: 캐시된 중간 결과 활용

---

## 📅 예상 일정

| 작업 | 예상 시간 | 상태 |
|------|-----------|------|
| 계획서 작성 | 30분 | ✅ 완료 |
| 연결 코드 개발 | 2시간 | ⏳ 진행 예정 |
| 시각화 구현 | 1시간 | ⏳ 진행 예정 |
| 테스트 | 30분 | ⏳ 진행 예정 |
| **총 소요 시간** | **4시간** | |

---

## 📝 참고사항

### 사용 라이브러리
- matplotlib 3.5.1
- seaborn 0.11.2
- pandas 1.4.2
- numpy 1.22.3

### 코드 스타일
- PEP 8 준수
- 함수별 docstring 작성
- 타입 힌트 사용

---

*작성일: 2025-09-19*
*작성자: 프로젝트 팀*