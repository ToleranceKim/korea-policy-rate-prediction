#!/bin/bash
# 뉴스 데이터 수집 스크립트

echo "=========================================="
echo "뉴스 데이터 수집 시작: $(date)"
echo "=========================================="

# 프로젝트 루트로 이동
cd /Users/lord_jubin/Desktop/my_git/korea-policy-rate-prediction
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate ds_env

# 수집할 연도 설정
for year in 2021 2022 2023 2024 2025; do
    echo ""
    echo "[${year}년 수집 시작]"
    python crawler/scripts/run.py yearly ${year}
    
    # 연도 간 대기 시간
    if [ $year -lt 2025 ]; then
        echo "다음 연도 수집 전 60초 대기..."
        sleep 60
    fi
done

echo ""
echo "=========================================="
echo "뉴스 데이터 수집 완료: $(date)"
echo "=========================================="