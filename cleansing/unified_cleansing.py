#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
unified_cleansing.py
모든 데이터 소스(뉴스, MPB, 채권)에 대한 통합 정제 스크립트
"""

import re
import json
import pandas as pd
import glob
import os
import sys
import argparse
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

class DataCleaner:
    """통합 데이터 정제 클래스"""

    def __init__(self):
        """정제 패턴 초기화"""
        # 뉴스 정제 패턴 (연합뉴스 기준 - 가장 엄격)
        self.news_patterns = {
            'email': r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)',
            'byline_yonhap': r'\([^\)]+=\s*연합뉴스\)\s*[^=]+ =',
            'byline_edaily': r'\[이데일리\s+[^\]]+\s+기자\]',
            'byline_infomax': r'\([^=]+=연합인포맥스\)\s*[^=]+ =',
            'tags': r'\[[^\[\]]*(연합뉴스|자료사진|AFP|재판매|DB금지|사진|표|그래프)[^\[\]]*\]',
            'stock_code': r'\(\d{6}\)|\[\s*\d{6}\s*\]',
            'special_chars': r'[▲△▶▼▽◆◇=ㆍ/·;:!?\'"''""~&]',
            'javascript': r'function\([^)]*\)\s*\{[^}]*\}',
            'url': r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            'parenthesis_content': r'\([^)]*제공[^)]*\)|\([^)]*사진[^)]*\)',
        }

        # MPB 정제 패턴
        self.mpb_patterns = {
            'stock_code': r'\(\d{6}\)',
            'ad_text': r'▶\s*관련기사\s*◀',
            'arrow_text': r'☞[^☞]*',
            'list_number': r'^\d+\.\s+',
            'news_summary': r'<간추린 소식>[^-]*',
            'special_chars': r'[▲△▶▼▽◆◇=ㆍ/·.,;:!?\'"''""~∼&()→%․\[\]\-–]',
            'photo_table': r'사진|표',
            'multiple_spaces': r'\s+',
        }

        # 채권 정제 패턴
        self.bond_patterns = {
            'html_tags': r'<[^>]*>',
            'email': r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)',
            'korean_jamo': r'([ㄱ-ㅎㅏ-ㅣ]+)',
            'decimal_numbers': r'\d+\.\d+',
            'numbers': r'\d+',
            'special_chars': r'[^a-zA-Z0-9ㄱ-ㅣ가-힣\s]',
            'multiple_spaces': r'\s+',
        }

        # 정제된 데이터 저장 경로
        self.output_dir = PROJECT_ROOT / 'cleansing' / 'cleaned_data'
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def clean_text_news(self, text):
        """뉴스 텍스트 정제"""
        if pd.isna(text) or text == '':
            return ''

        # 순서 중요: 특정 패턴부터 일반 패턴으로
        for pattern_name, pattern in self.news_patterns.items():
            text = re.sub(pattern, ' ', text)

        # 공백 정리
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def clean_text_mpb(self, text):
        """MPB 텍스트 정제"""
        if pd.isna(text) or text == '':
            return ''

        for pattern_name, pattern in self.mpb_patterns.items():
            if pattern_name == 'list_number':
                text = re.sub(pattern, '', text, flags=re.MULTILINE)
            else:
                text = re.sub(pattern, ' ', text)

        # 공백 정리
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def clean_text_bond(self, text):
        """채권 텍스트 정제"""
        if pd.isna(text) or text == '':
            return ''

        for pattern_name, pattern in self.bond_patterns.items():
            text = re.sub(pattern, ' ', text)

        # 공백 정리
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def clean_news_data(self):
        """뉴스 데이터 정제 (359K articles)"""
        print("="*60)
        print("뉴스 데이터 정제 시작")
        print("="*60)

        news_files = glob.glob(str(PROJECT_ROOT / 'crawler/data/unified/news_*.json'))
        news_files = sorted([f for f in news_files if 'summary' not in f])

        print(f"처리할 파일 수: {len(news_files)}")

        cleaned_news_dir = self.output_dir / 'news_cleaned'
        cleaned_news_dir.mkdir(exist_ok=True)

        total_articles = 0
        cleaned_articles = 0
        removed_duplicates = 0

        for file_path in tqdm(news_files, desc="뉴스 파일 처리"):
            filename = os.path.basename(file_path)

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            cleaned_data = {}

            # 각 언론사별 처리
            for source in ['yonhap', 'edaily', 'infomax']:
                if source not in data:
                    continue

                articles = data[source]
                cleaned_articles_list = []
                seen_contents = set()  # 중복 제거용

                for article in articles:
                    total_articles += 1

                    # 제목과 내용 정제
                    cleaned_title = self.clean_text_news(article.get('title', ''))
                    cleaned_content = self.clean_text_news(article.get('content', ''))

                    # 중복 체크 (제목+내용)
                    content_hash = f"{cleaned_title}_{cleaned_content}"
                    if content_hash in seen_contents:
                        removed_duplicates += 1
                        continue

                    seen_contents.add(content_hash)

                    # 빈 내용 제외
                    if cleaned_content and len(cleaned_content) > 10:
                        cleaned_articles_list.append({
                            'date': article.get('date', ''),
                            'title': cleaned_title,
                            'content': cleaned_content,
                            'url': article.get('url', '')
                        })
                        cleaned_articles += 1

                cleaned_data[source] = cleaned_articles_list

            # 정제된 데이터 저장
            output_path = cleaned_news_dir / f"{filename.replace('.json', '_cleaned.json')}"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, ensure_ascii=False, indent=2)

        print(f"\n✓ 뉴스 정제 완료:")
        print(f"  - 전체 기사: {total_articles:,}")
        print(f"  - 정제된 기사: {cleaned_articles:,}")
        print(f"  - 제거된 중복: {removed_duplicates:,}")
        print(f"  - 정제율: {(cleaned_articles/total_articles)*100:.1f}%")

        return cleaned_articles

    def clean_mpb_data(self):
        """MPB 의사록 정제 (224 documents)"""
        print("\n" + "="*60)
        print("MPB 의사록 정제 시작")
        print("="*60)

        mpb_file = PROJECT_ROOT / 'data/mpb_complete.json'

        if not mpb_file.exists():
            print(f"MPB 파일을 찾을 수 없습니다: {mpb_file}")
            return 0

        with open(mpb_file, 'r', encoding='utf-8') as f:
            mpb_data = json.load(f)

        print(f"처리할 의사록: {len(mpb_data)}개")

        cleaned_mpb = []

        for item in tqdm(mpb_data, desc="MPB 의사록 처리"):
            cleaned_item = {
                'date': item.get('date', ''),
                'year': item.get('year', ''),
                'title': self.clean_text_mpb(item.get('title', '')),
                'content': self.clean_text_mpb(item.get('content', ''))
            }

            # 빈 내용 제외
            if cleaned_item['content'] and len(cleaned_item['content']) > 50:
                cleaned_mpb.append(cleaned_item)

        # 정제된 데이터 저장
        output_path = self.output_dir / 'mpb_cleaned.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_mpb, f, ensure_ascii=False, indent=2)

        print(f"\n✓ MPB 정제 완료:")
        print(f"  - 전체 의사록: {len(mpb_data)}")
        print(f"  - 정제된 의사록: {len(cleaned_mpb)}")
        print(f"  - 정제율: {(len(cleaned_mpb)/len(mpb_data))*100:.1f}%")

        return len(cleaned_mpb)

    def clean_bond_data(self):
        """채권 보고서 정제 (6,515 reports)"""
        print("\n" + "="*60)
        print("채권 보고서 정제 시작")
        print("="*60)

        bond_file = PROJECT_ROOT / 'data/auxiliary/bond_reports_consolidated.json'

        if not bond_file.exists():
            print(f"채권 파일을 찾을 수 없습니다: {bond_file}")
            return 0

        with open(bond_file, 'r', encoding='utf-8') as f:
            bond_data = json.load(f)

        print(f"처리할 보고서: {len(bond_data):,}개")

        cleaned_bonds = []

        for item in tqdm(bond_data, desc="채권 보고서 처리"):
            cleaned_item = {
                'date': item.get('date', ''),
                'title': self.clean_text_bond(item.get('title', '')),
                'content': self.clean_text_bond(item.get('content', '')),
                'link': item.get('link', '')
            }

            # 빈 내용 제외
            if cleaned_item['content'] and len(cleaned_item['content']) > 20:
                cleaned_bonds.append(cleaned_item)

        # 정제된 데이터 저장
        output_path = self.output_dir / 'bond_cleaned.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_bonds, f, ensure_ascii=False, indent=2)

        print(f"\n✓ 채권 정제 완료:")
        print(f"  - 전체 보고서: {len(bond_data):,}")
        print(f"  - 정제된 보고서: {len(cleaned_bonds):,}")
        print(f"  - 정제율: {(len(cleaned_bonds)/len(bond_data))*100:.1f}%")

        return len(cleaned_bonds)

    def clean_all(self):
        """모든 데이터 정제"""
        start_time = datetime.now()

        print("="*60)
        print("통합 데이터 정제 시작")
        print("="*60)

        # 각 데이터 소스 정제
        news_count = self.clean_news_data()
        mpb_count = self.clean_mpb_data()
        bond_count = self.clean_bond_data()

        elapsed = datetime.now() - start_time

        print("\n" + "="*60)
        print("통합 데이터 정제 완료")
        print("="*60)
        print(f"총 처리 시간: {elapsed.total_seconds()/60:.1f}분")
        print(f"총 정제 문서: {news_count + mpb_count + bond_count:,}개")
        print(f"저장 위치: {self.output_dir}")

        return news_count, mpb_count, bond_count

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='통합 데이터 정제')
    parser.add_argument('--type', choices=['all', 'news', 'mpb', 'bond'],
                       default='all', help='정제할 데이터 타입')
    args = parser.parse_args()

    cleaner = DataCleaner()

    if args.type == 'all':
        cleaner.clean_all()
    elif args.type == 'news':
        cleaner.clean_news_data()
    elif args.type == 'mpb':
        cleaner.clean_mpb_data()
    elif args.type == 'bond':
        cleaner.clean_bond_data()

    print("\n✅ 정제 작업 완료!")

if __name__ == "__main__":
    main()