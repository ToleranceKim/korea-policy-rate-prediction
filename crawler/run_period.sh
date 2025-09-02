#!/bin/bash

cd /Users/lord_jubin/Desktop/my_git/mpb-stance-mining/crawler
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate ds_env

for year in 2021 2022 2023 2024 2025; do
    echo "${year}년 수집 시작"
    python scripts/run.py yearly ${year}
    sleep 60
done

echo "완료"