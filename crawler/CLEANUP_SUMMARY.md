# 프로젝트 정리 요약

## 🗑️ 불필요한 파일 목록 (총 15개)

### 중복 파일 (2개)
- `scripts/batch/run_batch_collection.py` - 구버전, 루트 버전 사용
- `crawler.md` - TECHNICAL_DOCUMENTATION.md로 대체

### 일회성 스크립트 (2개)
- `cleanup_project.py` - 프로젝트 정리 완료
- `fix_paths.py` - 경로 수정 완료

### 개발용 노트북 (3개)
- `InfoMax/crawl_0816.ipynb`
- `edaily/edaily_crawler.ipynb`
- `yh/news_crawler_yh_fixed.ipynb`

### 구버전 스파이더 (3개)
- `yh/yh_crawler/yh_crawler/spiders/yh_spider.py`
- `edaily/edaily_crawler/edaily_crawler/spiders/edaily_spider.py`
- `InfoMax/infomax_crawler/infomax_crawler/spiders/infomax_spider.py`

### 연구용 스크립트 (1개)
- `scripts/utils/research_yonhap_historical.py`

### 테스트 파일 (4개) - 이미 아카이브됨
- `archive/test_outputs/debug_infomax.py`
- `archive/test_outputs/debug_news.py`
- `archive/test_outputs/test_article_content.py`
- 기타 테스트 JSON 파일들

## ✅ 유지해야 할 핵심 파일

### 배치 시스템
- `run_batch_collection.py` (루트)
- `scripts/batch/batch_collector.py`
- `scripts/batch/data_merger.py`

### 활성 크롤러
- `*_fixed.py` 스파이더들 (개선된 버전)
- `bond_crawling.py` (채권 크롤러)
- 각 크롤러의 `settings.py`

### 문서
- `TECHNICAL_DOCUMENTATION.md` - 기술 문서
- 각 디렉터리의 `README.md`

## 📁 최적 디렉터리 구조

```
crawler/
├── run_batch_collection.py      # 메인 실행 스크립트
├── TECHNICAL_DOCUMENTATION.md   # 기술 문서
├── .env.example                  # 환경 설정 템플릿
│
├── scripts/batch/               # 배치 시스템
│   ├── batch_collector.py
│   └── data_merger.py
│
├── data/                        # 데이터 계층
│   ├── raw/
│   ├── processed/
│   ├── monthly/
│   └── merged/
│
├── logs/                        # 로그 파일
│
├── archive/                     # 아카이브
│   ├── setup_scripts/          # 일회성 스크립트
│   ├── old_spiders/            # 구버전 스파이더
│   ├── development_notebooks/  # 개발 노트북
│   ├── research_scripts/       # 연구 스크립트
│   ├── test_outputs/           # 테스트 출력
│   ├── bond_csvs/              # 과거 CSV 데이터
│   └── bond_pdfs/              # 과거 PDF 파일
│
└── [크롤러 디렉터리들]/
    ├── yh/
    ├── edaily/
    ├── InfoMax/
    ├── BOND/
    ├── MPB/
    ├── interest_rates/
    └── call_ratings/
```

## 🚀 정리 실행 방법

```bash
# 1. 백업
git add -A && git commit -m "Before cleanup"

# 2. 정리 스크립트 실행
chmod +x final_cleanup.sh
./final_cleanup.sh

# 3. 결과 확인
ls -la archive/
```

## ⚠️ 주의사항

1. **경로 하드코딩**
   - `/opt/anaconda3/envs/ds_env/` → `.env` 파일로 설정 필요

2. **디렉터리명 불일치**
   - `yh`, `InfoMax`, `BOND` → 소문자 통일 권장

3. **미사용 Scrapy 파일**
   - `items.py`, `pipelines.py`, `middlewares.py`는 대부분 템플릿 상태
   - 필요시 추후 구현 가능

## 📊 정리 효과

- **파일 수 감소**: 15개 파일 제거/아카이브
- **구조 단순화**: 중복 제거, 계층 명확화
- **유지보수성 향상**: 활성 코드만 남김
- **가독성 개선**: 명확한 디렉터리 구조

## ✅ 최종 상태

정리 후 프로젝트는:
- **프로덕션 준비 완료**
- **체계적인 구조**
- **확장 가능한 설계**
- **문서화 완비**

상태로 즉시 대규모 데이터 수집이 가능합니다.