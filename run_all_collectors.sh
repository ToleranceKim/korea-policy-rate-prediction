#!/bin/bash

# 자동 데이터 수집 스크립트
# MPB 의사록과 채권 리포트를 병렬로 수집

echo "=========================================="
echo "데이터 수집 시작: $(date)"
echo "=========================================="

# 환경 설정
cd /Users/lord_jubin/Desktop/my_git/mpb-stance-mining
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate ds_env

# 1. MPB 의사록 수집 (백그라운드)
echo ""
echo "[1/3] MPB 의사록 수집 시작..."
cd crawler/MPB
nohup /opt/anaconda3/envs/ds_env/bin/scrapy crawl mpb_crawler_perfect \
    -a start_year=2014 \
    -a end_year=2025 \
    -o ../../data/mpb_complete_$(date +%Y%m%d).json \
    -s LOG_LEVEL=INFO \
    -s CLOSESPIDER_PAGECOUNT=200 > mpb_collection.log 2>&1 &
MPB_PID=$!
echo "MPB 크롤러 실행 중 (PID: $MPB_PID)"

# 2. 기준금리 데이터 재수집
echo ""
echo "[2/3] 기준금리 데이터 수집..."
cd ../interest_rates
/opt/anaconda3/envs/ds_env/bin/scrapy crawl interest_rates_complete \
    -a start_year=2014 \
    -a end_year=2025 \
    -o ../../data/interest_rates_complete_$(date +%Y%m%d).json \
    -s LOG_LEVEL=INFO

# 3. 채권 리포트 수집 (월별 병렬)
echo ""
echo "[3/3] 채권 리포트 수집 시작..."
cd ../BOND

# 연도별 월별 수집 함수
collect_bonds_for_year() {
    year=$1
    echo "  ${year}년 채권 리포트 수집 중..."
    
    for month in {1..12}; do
        # 월 형식 맞추기 (01, 02, ...)
        month_str=$(printf "%02d" $month)
        
        # 마지막 날 계산
        if [ $month -eq 12 ]; then
            last_day=31
        elif [ $month -eq 2 ]; then
            # 윤년 체크
            if [ $((year % 4)) -eq 0 ] && [ $((year % 100)) -ne 0 ] || [ $((year % 400)) -eq 0 ]; then
                last_day=29
            else
                last_day=28
            fi
        elif [ $month -eq 4 ] || [ $month -eq 6 ] || [ $month -eq 9 ] || [ $month -eq 11 ]; then
            last_day=30
        else
            last_day=31
        fi
        
        start_date="${year}-${month_str}-01"
        end_date="${year}-${month_str}-${last_day}"
        
        echo "    수집 중: ${start_date} ~ ${end_date}"
        /opt/anaconda3/envs/ds_env/bin/python bond_parallel_crawler.py $start_date $end_date 5
        
        # 서버 부하 방지를 위한 대기
        sleep 10
    done
}

# 2024년부터 시작 (테스트)
for year in 2024 2023 2022 2021 2020 2019 2018 2017 2016 2015 2014; do
    collect_bonds_for_year $year &
    
    # 동시에 3개 연도까지만 처리
    while [ $(jobs -r | wc -l) -ge 3 ]; do
        sleep 30
    done
done

# 모든 백그라운드 작업 완료 대기
echo ""
echo "모든 수집 작업 완료 대기 중..."
wait

echo ""
echo "=========================================="
echo "데이터 수집 완료: $(date)"
echo "=========================================="

# 수집 결과 확인
echo ""
echo "수집 결과:"
echo "----------"

# MPB 의사록 개수
if [ -f "../../data/mpb_complete_$(date +%Y%m%d).json" ]; then
    mpb_count=$(cat ../../data/mpb_complete_$(date +%Y%m%d).json | grep -c '"title"')
    echo "MPB 의사록: ${mpb_count}개"
fi

# 채권 리포트 개수
bond_count=$(find ../../data/bond_reports -name "*.json" 2>/dev/null | wc -l)
echo "채권 리포트 파일: ${bond_count}개"

# PDF 파일 개수
pdf_count=$(find ../../data/bond_reports -name "*.pdf" 2>/dev/null | wc -l)
echo "PDF 파일: ${pdf_count}개"

echo ""
echo "로그 파일 위치:"
echo "  - MPB: crawler/MPB/mpb_collection.log"
echo "  - 채권: crawler/BOND/bond_collection_*.log"