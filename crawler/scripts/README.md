# 논문 재현 크롤러 (최종 버전)

"Deciphering Monetary Policy Board Minutes through Text Mining Approach" 논문의 데이터 수집을 위한 통합 크롤러입니다.

## 📌 최종 파이프라인

**`final_paper_reproduction_crawler_2014_2025.py`** - 논문 재현을 위한 유일한 공식 크롤러

### 주요 특징
- **기간**: 2014년 1월 ~ 2025년 8월 (데이터 접근성 고려)
- **대상**: 연합뉴스(25%), 이데일리(33%), 연합인포맥스(42%)
- **추가 데이터**: MPB 회의록, 채권 리포트, 콜금리
- **버전**: 3.0 (2025-08-26 최종)

## 빠른 시작

### 테스트 실행 (권장)
```bash
/opt/anaconda3/envs/ds_env/bin/python final_paper_reproduction_crawler_2014_2025.py --test
```

### 전체 데이터 수집
```bash
/opt/anaconda3/envs/ds_env/bin/python final_paper_reproduction_crawler_2014_2025.py
```

### 브라우저 표시 모드
```bash
/opt/anaconda3/envs/ds_env/bin/python final_paper_reproduction_crawler_2014_2025.py --test --show-browser
```

## 파일 구성

```
scripts/
├── README.md                                      # 이 파일
├── USAGE_GUIDE.md                                # 상세 사용 가이드
├── final_paper_reproduction_crawler_2014_2025.py # 최종 파이프라인
└── final_paper_reproduction.log                  # 실행 로그
```

## 출력 위치
`/crawler/data/paper_reproduction/`

## ⚠️ 중요 안내

이전 버전들은 모두 `/crawler/archive/old_pipelines/`로 이동되었습니다.
**오직 이 디렉토리의 스크립트만 사용하세요.**

상세한 사용법은 [USAGE_GUIDE.md](USAGE_GUIDE.md)를 참조하세요.