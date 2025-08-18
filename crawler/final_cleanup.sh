#!/bin/bash

# MPB Stance Mining Crawler - 최종 정리 스크립트
# 실행 전 반드시 백업하세요!

echo "🧹 최종 프로젝트 정리 시작..."

# 1. 중복 파일 제거
echo "📄 중복 파일 제거..."
rm -f scripts/batch/run_batch_collection.py  # 구버전, 루트 버전 사용
rm -f crawler.md  # TECHNICAL_DOCUMENTATION.md로 대체

# 2. 일회성 유틸리티 아카이브
echo "📦 일회성 스크립트 아카이브..."
mkdir -p archive/setup_scripts
mv cleanup_project.py archive/setup_scripts/ 2>/dev/null
mv fix_paths.py archive/setup_scripts/ 2>/dev/null

# 3. Jupyter notebooks 아카이브
echo "📓 개발용 노트북 아카이브..."
mkdir -p archive/development_notebooks
find . -name "*.ipynb" -exec mv {} archive/development_notebooks/ \; 2>/dev/null

# 3-1. 구버전 스파이더 아카이브
echo "🕷️ 구버전 스파이더 아카이브..."
mkdir -p archive/old_spiders
mv yh/yh_crawler/yh_crawler/spiders/yh_spider.py archive/old_spiders/ 2>/dev/null
mv edaily/edaily_crawler/edaily_crawler/spiders/edaily_spider.py archive/old_spiders/ 2>/dev/null
mv InfoMax/infomax_crawler/infomax_crawler/spiders/infomax_spider.py archive/old_spiders/ 2>/dev/null

# 3-2. 연구용 스크립트 아카이브
echo "🔬 연구용 스크립트 아카이브..."
mkdir -p archive/research_scripts
mv scripts/utils/research_yonhap_historical.py archive/research_scripts/ 2>/dev/null

# 4. 빈 디렉터리 생성 확인
echo "📁 필수 디렉터리 확인..."
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/monthly
mkdir -p data/merged
mkdir -p logs
mkdir -p scripts/batch
mkdir -p scripts/utils

# 5. 권한 설정
echo "🔐 실행 권한 설정..."
chmod +x run_batch_collection.py
chmod +x scripts/batch/*.py

# 6. 불필요한 __pycache__ 제거
echo "🗑️ 캐시 파일 정리..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

echo "✅ 정리 완료!"
echo ""
echo "📊 정리 결과:"
echo "- 중복 파일 제거됨"
echo "- 일회성 스크립트 아카이브됨" 
echo "- 개발 노트북 아카이브됨"
echo "- 디렉터리 구조 최적화됨"
echo ""
echo "⚠️  주의사항:"
echo "1. /opt/anaconda3 경로는 시스템에 맞게 수정 필요"
echo "2. 크롤러 디렉터리명 통일 권장 (소문자)"
echo "3. 실행 전 git commit 권장"