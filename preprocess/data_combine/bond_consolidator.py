#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
bond_consolidator.py
6,515개의 채권 보고서 CSV 파일을 하나의 JSON으로 통합
"""

import pandas as pd
import json
import os
import glob
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# 프로젝트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
BOND_CSV_DIR = PROJECT_ROOT / "crawler/archive/bond_csvs"
OUTPUT_FILE = PROJECT_ROOT / "data/auxiliary/bond_reports_consolidated.json"

def consolidate_bond_csvs():
    """모든 채권 CSV 파일을 통합"""
    print("="*60)
    print("Bond Report CSV Consolidation")
    print("="*60)

    # CSV 파일 목록 가져오기
    csv_files = glob.glob(str(BOND_CSV_DIR / "*.csv"))
    print(f"Found {len(csv_files)} CSV files")

    all_bonds = []
    error_files = []

    # 프로그레스 바와 함께 처리
    for csv_file in tqdm(csv_files, desc="Processing CSV files"):
        try:
            # CSV 읽기
            df = pd.read_csv(csv_file)

            # 필수 컬럼 확인
            required_cols = ['Date', 'Title', 'Content']
            if all(col in df.columns for col in required_cols):
                # 각 행을 딕셔너리로 변환
                for _, row in df.iterrows():
                    # 날짜 형식 표준화
                    try:
                        date_str = str(row['Date'])
                        # YYYY.MM.DD 형식을 YYYY-MM-DD로 변경
                        if '.' in date_str:
                            date_str = date_str.replace('.', '-')

                        bond_data = {
                            'date': date_str,
                            'title': str(row['Title']),
                            'content': str(row['Content']),
                            'link': str(row.get('Link', ''))
                        }

                        # Content가 비어있지 않은 경우만 추가
                        if bond_data['content'] and bond_data['content'] != 'nan':
                            all_bonds.append(bond_data)
                    except Exception as e:
                        continue
            else:
                error_files.append((csv_file, "Missing required columns"))

        except Exception as e:
            error_files.append((csv_file, str(e)))

    # 날짜순 정렬
    all_bonds.sort(key=lambda x: x['date'])

    # 결과 출력
    print(f"\nProcessing complete:")
    print(f"  ✓ Successfully processed: {len(csv_files) - len(error_files)} files")
    print(f"  ✓ Total bond reports: {len(all_bonds)}")
    print(f"  ✗ Failed files: {len(error_files)}")

    if error_files:
        print("\nFirst 10 error files:")
        for file, error in error_files[:10]:
            print(f"  - {Path(file).name}: {error}")

    # JSON으로 저장
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_bonds, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Saved consolidated data to: {OUTPUT_FILE}")

    # 통계 정보
    if all_bonds:
        dates = [bond['date'] for bond in all_bonds]
        print(f"\nDate range: {min(dates)} to {max(dates)}")

        # 연도별 분포
        years = {}
        for date in dates:
            year = date.split('-')[0]
            years[year] = years.get(year, 0) + 1

        print("\nDistribution by year:")
        for year in sorted(years.keys()):
            print(f"  {year}: {years[year]} reports")

    return len(all_bonds)

if __name__ == "__main__":
    consolidate_bond_csvs()
    print("\n" + "="*60)
    print("✅ Bond consolidation completed!")
    print("="*60)