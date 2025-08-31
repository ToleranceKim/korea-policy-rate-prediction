# 뉴스 크롤러 실행 스크립트

## 통합 실행 스크립트

**`run.py`** - 모든 뉴스 크롤링을 위한 통합 스크립트

### 빠른 시작

```bash
# 테스트 (최근 3일)
python run.py test

# 월별 크롤링
python run.py monthly 2015 1

# 연도별 크롤링 (안전 모드)
python run.py yearly 2015 --safe

# 크롤링 재개
python run.py resume 2015 7 --safe

# 데이터 병합
python run.py merge
```

### 주요 특징
- **통합 관리**: 하나의 스크립트로 모든 기능
- **안전 모드**: 네이버 검색 제한 우회 (`--safe`)
- **유연한 실행**: 테스트, 월별, 연도별, 재개
- **자동 재시도**: 실패 시 자동 재시도 메커니즘

## 파일 구조

```
scripts/
├── README.md        # 이 파일
├── run.py          # 통합 실행 스크립트
└── USAGE_GUIDE.md  # 상세 사용 가이드
```

## 데이터 위치
- **일반 모드**: `/crawler/data/unified/`
- **안전 모드**: `/crawler/data/safe/`

상세한 사용법은 [USAGE_GUIDE.md](USAGE_GUIDE.md) 또는 상위 [README.md](../README.md)를 참조하세요.