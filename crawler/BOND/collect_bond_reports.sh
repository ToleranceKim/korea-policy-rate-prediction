#!/bin/bash
# 채권 리포트 수집 스크립트

echo "채권 리포트 수집 시작..."
python bond_crawling.py

echo "채권 리포트 수집 완료!"
echo "수집된 파일: dataset_2/*.csv"