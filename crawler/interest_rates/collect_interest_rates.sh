#!/bin/bash
# 콜금리 데이터 수집 스크립트

echo "콜금리 데이터 수집 시작..."
scrapy crawl interest_rates \
    -o ../../data/auxiliary/call_rates_2014_2025.csv

echo "콜금리 수집 완료!"