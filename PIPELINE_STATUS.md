# 한국은행 기준금리 예측 파이프라인 - 실행 현황

## 🎯 목표
실제 데이터(359K 뉴스, 224 MPB 의사록, 6.5K 채권 리포트)를 사용하여 NBC 모델 학습

## ✅ 완료된 작업

### 1. 데이터 정제 (완료)
- **unified_cleansing.py** 생성 - 통합 정제 스크립트
- 연합뉴스 기준으로 가장 엄격한 정제 적용
- 362,849개 문서 정제 완료
- 위치: `cleansing/cleaned_data/`

### 2. Corpus 생성 (완료)
- **corpus_data_fixed.py** 수정 - 실제 정제 데이터 경로 연결
- 콜금리 기반 라벨링 (2개월 선행)
- 122,315개 레코드 생성 (라벨 균형: Dovish 48.5%, Hawkish 51.5%)
- 위치: `preprocess/data_combine/corpus_data.csv`

### 3. 토큰화 (완료)
- eKoNLPy/Mecab 사용
- 10개 배치로 나누어 처리
- 122,315개 문서 토큰화
- 위치: `preprocess/tokenization/corpus_tokenized_*.csv`

### 4. N-gram 추출 (완료)
- 1-5 gram 추출
- POS 필터링 (NNG, VA, MAG, VV, VCN)
- 143M n-grams 추출 (60M unique)
- 위치: `preprocess/ngram/ngram_results.csv`

### 5. N-gram 필터링 (완료)
- 최소 빈도 5 이상 필터링
- 1.9M n-grams로 축소
- 위치: `modeling/nbc/filtered_ngrams.csv`

### 6. 더미 데이터 제거 (완료)
- 랜덤 생성된 더미 데이터 파일 삭제
- date_label.json, date_ngram.json, nbc_model.pkl 등

### 7. 실제 데이터 연결 스크립트 작성 (완료)
- **create_real_model_data.py** 생성
- corpus_data.csv의 실제 라벨과 n-gram 연결
- **nbc_modeling.py** 수정 - real 데이터 사용하도록 변경

## 🔄 진행 중인 작업

### 8. 실제 모델 데이터 생성 (진행 중)
- 72M filtered n-grams 처리 중
- 진행률: ~1% (예상 완료 시간: 45분)
- 백그라운드 프로세스 ID: 27b340
- 출력 파일:
  - date_label_real.json
  - date_ngram_real.json
  - model_data_stats.json

## ⏳ 대기 중인 작업

### 9. NBC 모델 학습
- 실제 데이터로 학습 예정
- 모델 데이터 생성 완료 후 실행

## 📊 주요 발견 사항

### 문제점 발견
- **create_model_data.py**가 랜덤 더미 데이터 생성하고 있었음
- 실제 corpus 라벨을 사용하지 않아 성능 저하
- 이전 프로젝트에서 테스트 코드가 그대로 사용됨

### 해결 방안
1. 더미 데이터 파일 모두 제거 ✅
2. 실제 데이터 연결 로직 구현 ✅
3. 모델 재학습 예정 ⏳

## 🚀 실행 방법

### 전체 파이프라인 실행
```bash
./run_real_pipeline.sh
```

### 개별 단계 실행
```bash
# 1. 정제
cd cleansing
python unified_cleansing.py --type all

# 2. Corpus 생성
cd preprocess/data_combine
python corpus_data_fixed.py

# 3. 토큰화
cd preprocess/tokenization
python tokenization_test.py

# 4. N-gram 추출
cd preprocess/ngram
python ngram_execute_test.py

# 5. N-gram 필터링
python ngram_counter.py

# 6. 실제 모델 데이터 생성
cd modeling/nbc
python create_real_model_data.py

# 7. NBC 모델 학습
python nbc_modeling.py
```

## 📈 데이터 통계

| 단계 | 입력 | 출력 | 축소율 |
|------|------|------|--------|
| 수집 | - | 362,849 문서 | - |
| 정제 | 362,849 | 362,849 (노이즈 제거) | 0% |
| Corpus | 362,849 | 122,315 레코드 | 66% |
| N-gram 추출 | 122,315 | 143M n-grams | - |
| 필터링 | 143M | 1.9M n-grams | 98.7% |

## 🔍 모니터링

### 백그라운드 프로세스 확인
```bash
# 실행 중인 프로세스 목록
ps aux | grep python

# 모델 데이터 생성 진행 상황
tail -f /path/to/log
```

### 생성된 파일 확인
```bash
# NBC 디렉토리
ls -la modeling/nbc/

# 실제 데이터 파일
ls -la modeling/nbc/*_real.json
```

## 📝 참고사항

- 모든 스크립트는 `_test.py`로 끝나지만 실제 데이터 처리
- 토큰화와 N-gram 추출이 가장 시간 소요 (각 40-60분, 60-90분)
- 메모리 사용량 주의 (특히 N-gram 처리 시)

---

*최종 업데이트: 2025-09-20 23:00*