#!/bin/bash
# MPB 의사록 수집 스크립트

echo "MPB 의사록 수집 시작..."
scrapy crawl mpb_crawler_perfect \
    -a start_year=2014 \
    -a end_year=2025 \
    -o ../../data/auxiliary/mpb_minutes_2014_2025.json

echo "MPB 수집 완료!"