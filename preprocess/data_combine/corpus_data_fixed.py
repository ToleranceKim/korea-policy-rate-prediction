#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
corpus_data_fixed.py
모든 데이터 소스를 통합하여 corpus_data.csv 생성
실제 존재하는 파일 경로 사용
"""

import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from datetime import datetime
import glob

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent

def load_news_data():
    """뉴스 데이터 로드 (정제된 JSON 파일들)"""
    print("Loading cleaned news data from JSON files...")

    news_files = glob.glob(str(PROJECT_ROOT / "cleansing/cleaned_data/news_cleaned/*_cleaned.json"))
    all_news = []

    for file in sorted(news_files):
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)

            # Process each source (yonhap, edaily, infomax)
            for source_name, articles in data.items():
                if isinstance(articles, list):
                    for item in articles:
                        all_news.append({
                            'Date': item.get('date'),
                            'Title': item.get('title'),
                            'Content': item.get('content'),
                            'Link': item.get('url'),
                            'source': source_name if source_name in ['yonhap', 'edaily', 'infomax'] else
                                     ('infomax' if 'infomax' in item.get('url', '') else
                                     ('edaily' if 'edaily' in item.get('url', '') else 'yh'))
                        })

    df_news = pd.DataFrame(all_news)
    # Remove empty content
    df_news = df_news[df_news['Content'].notna() & (df_news['Content'] != '')]
    print(f"Loaded {len(df_news)} news articles")
    return df_news

def load_bond_data():
    """채권 리포트 데이터 로드 (정제된 데이터)"""
    print("Loading cleaned bond report data...")

    bond_file = PROJECT_ROOT / "cleansing/cleaned_data/bond_cleaned.json"

    if bond_file.exists():
        try:
            with open(bond_file, 'r', encoding='utf-8') as f:
                bond_data = json.load(f)

            # 채권 데이터를 DataFrame으로 변환
            bond_records = []
            for item in bond_data:
                bond_records.append({
                    'Date': pd.to_datetime(item.get('date', ''), errors='coerce'),
                    'Title': item.get('title', ''),
                    'Content': item.get('content', ''),
                    'Link': item.get('link', ''),
                    'source': 'bond'
                })

            df_bond = pd.DataFrame(bond_records)
            # Remove empty content
            df_bond = df_bond[df_bond['Content'].notna() & (df_bond['Content'] != '')]
            print(f"Loaded {len(df_bond)} bond reports")
            return df_bond
        except Exception as e:
            print(f"Error loading bond report data: {e}")
            return pd.DataFrame(columns=['Date', 'Title', 'Content', 'Link', 'source'])
    else:
        print("Bond report data not found")
        return pd.DataFrame(columns=['Date', 'Title', 'Content', 'Link', 'source'])

def load_mpb_data():
    """MPB 의사록 데이터 로드"""
    print("Loading MPB minutes data...")

    mpb_file = PROJECT_ROOT / "cleansing/cleaned_data/mpb_cleaned.json"

    if mpb_file.exists():
        try:
            with open(mpb_file, 'r', encoding='utf-8') as f:
                mpb_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error loading MPB JSON file: {e}")
            print("Skipping MPB data...")
            return pd.DataFrame(columns=['Date', 'Title', 'Content', 'Link', 'source'])

        # MPB 데이터 구조 확인 및 변환
        mpb_records = []
        for item in mpb_data:
            # 날짜 포맷 통일
            date_str = item.get('date', '')
            if date_str:
                date_obj = pd.to_datetime(date_str, errors='coerce')
            else:
                date_obj = pd.NaT

            # Content 필드: content가 있으면 사용, 없으면 discussion + decision 사용
            content = item.get('content', '')
            if not content:
                discussion = item.get('discussion', '')
                decision = item.get('decision', '')
                content = f"{discussion}\n{decision}" if discussion or decision else ''

            mpb_records.append({
                'Date': date_obj,
                'Title': item.get('title', ''),
                'Content': content,
                'Link': item.get('pdf_url', ''),
                'source': 'mpb'
            })

        df_mpb = pd.DataFrame(mpb_records)
        # Remove empty content
        df_mpb = df_mpb[df_mpb['Content'].notna() & (df_mpb['Content'] != '')]
        print(f"Loaded {len(df_mpb)} MPB minutes")
        return df_mpb
    else:
        print("MPB data not found, creating empty dataframe")
        return pd.DataFrame(columns=['Date', 'Title', 'Content', 'Link', 'source'])

def load_call_rates():
    """콜금리 데이터 로드"""
    print("Loading call rates data...")

    call_file = PROJECT_ROOT / "crawler/data/auxiliary/market_call_rates_daily_2014_2025.csv"

    if call_file.exists():
        df_call = pd.read_csv(call_file)
        # 컬럼명 표준화 (날짜 -> Date, 콜금리 -> Call_Rate)
        df_call = df_call.rename(columns={'날짜': 'Date', '콜금리': 'Call_Rate'})
        # Date 컬럼 datetime으로 변환
        df_call['Date'] = pd.to_datetime(df_call['Date'])
        print(f"Loaded call rates data: {len(df_call)} records")
        return df_call
    else:
        print("Call rates data not found!")
        return None

def get_effective_rate(date, df_call):
    """특정 날짜에 유효한 금리를 찾기 (가장 가까운 이전 변경일의 금리)"""
    if df_call is None or df_call.empty:
        return None

    # 해당 날짜 이전의 가장 최근 금리 변경일 찾기
    past_rates = df_call[df_call['Date'] <= date]
    if past_rates.empty:
        return None

    # 가장 최근 금리 반환
    return past_rates.iloc[-1]['Call_Rate']

def calculate_label(article_date, df_call):
    """콜금리 변동 기반 라벨 계산 (논문 재현)"""
    if df_call is None:
        return None

    # 현재 날짜의 유효 금리
    current_rate = get_effective_rate(article_date, df_call)
    if current_rate is None:
        return None

    # 1개월 후의 유효 금리 (논문과 동일)
    future_date = article_date + pd.DateOffset(months=1)
    future_rate = get_effective_rate(future_date, df_call)
    if future_rate is None:
        return None

    # 금리 변동 계산
    difference = future_rate - current_rate

    # Hawkish(1): 금리 인상, Dovish(0): 금리 인하 (논문과 동일한 ±3bp 임계값)
    if difference > 0.03:
        return 1
    elif difference < -0.03:
        return 0
    else:
        return None  # 변동 없음

def main():
    """메인 실행 함수"""
    print("="*60)
    print("Corpus Data Integration")
    print("="*60)

    # 1. 데이터 로드
    df_news = load_news_data()
    df_bond = load_bond_data()
    df_mpb = load_mpb_data()
    df_call = load_call_rates()

    # 2. 날짜 형식 통일
    print("\nStandardizing date formats...")
    df_news['Date'] = pd.to_datetime(df_news['Date'], errors='coerce')
    df_bond['Date'] = pd.to_datetime(df_bond['Date'], errors='coerce')

    # 3. 데이터 통합
    print("\nCombining all data sources...")
    df_corpus = pd.concat([df_news, df_bond, df_mpb], ignore_index=True)

    # 4. Primary Key 생성
    print("\nGenerating primary keys...")
    pk_dict = {'yonhap': '1', 'edaily': '2', 'infomax': '3', 'bond': '4', 'mpb': '5'}
    df_corpus['counter'] = df_corpus.groupby(['source', 'Date']).cumcount() + 1
    df_corpus['source_num'] = df_corpus['source'].map(pk_dict)

    # PK 생성 전 source_num NaN 체크
    nan_source = df_corpus['source_num'].isna().sum()
    if nan_source > 0:
        print(f"  WARNING: {nan_source} rows with unmapped source detected")
        unknown_sources = df_corpus[df_corpus['source_num'].isna()]['source'].unique()
        print(f"  Unknown sources: {unknown_sources}")
        df_corpus = df_corpus.dropna(subset=['source_num'])

    df_corpus['pk'] = (df_corpus['source_num'] +
                      df_corpus['Date'].dt.strftime('%Y%m%d') +
                      df_corpus['counter'].apply(lambda x: f'{x:03}'))

    # 5. 라벨 계산
    print("\nCalculating labels based on 1-month call rate changes (paper reproduction)...")
    if df_call is not None:
        # 진행 상황 출력을 위한 함수
        def calculate_with_progress(row):
            if row.name % 10000 == 0:
                print(f"  Progress: {row.name}/{len(df_corpus)} records processed...")
            return calculate_label(row['Date'], df_call)

        # 금리 데이터를 날짜순으로 정렬 (성능 향상)
        df_call = df_call.sort_values('Date')
        df_corpus['Label'] = df_corpus.apply(calculate_with_progress, axis=1)
    else:
        df_corpus['Label'] = None

    # 6. 필요한 컬럼만 선택
    df_final = df_corpus[['pk', 'Date', 'Title', 'Content', 'Label']]

    # 7. NaN 제거
    print(f"\nBefore removing NaN: {len(df_final)} records")
    df_final = df_final.dropna(subset=['Content', 'Label'])
    print(f"After removing NaN: {len(df_final)} records")

    # 8. 라벨 분포 확인
    if 'Label' in df_final.columns:
        label_counts = df_final['Label'].value_counts()
        print(f"\nLabel distribution:")
        print(f"  Dovish (0): {label_counts.get(0, 0)}")
        print(f"  Hawkish (1): {label_counts.get(1, 0)}")

    # 9. CSV 저장
    output_path = PROJECT_ROOT / "preprocess/data_combine/corpus_data.csv"
    df_final.to_csv(output_path, index=False, encoding='utf-8')
    print(f"\n✓ Saved corpus_data.csv with {len(df_final)} records")
    print(f"  Path: {output_path}")

    return df_final

if __name__ == "__main__":
    df = main()
    print("\n" + "="*60)
    print("✅ Corpus data integration completed!")
    print("="*60)