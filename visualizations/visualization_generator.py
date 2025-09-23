#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
visualization_generator.py
프로젝트 시각화 생성 모듈

생성되는 시각화:
1. N-gram Top 20 막대그래프
2. 성능 개선 곡선 (v1→v4)
3. 월별 뉴스 수집량 추이
4. 언론사별 비율 파이차트
5. 전처리 전후 데이터 크기 비교
"""

import json
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from pathlib import Path
import os
from datetime import datetime
import platform
import warnings

# 한글 폰트 설정
# matplotlib 초기화 전에 폰트 설정
if platform.system() == 'Darwin':  # Mac
    # macOS에서 한글 폰트 설정
    # 먼저 폰트 경로가 존재하는지 확인
    font_paths = [
        '/System/Library/Fonts/AppleSDGothicNeo.ttc',
        '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
        '/Library/Fonts/AppleGothic.ttf',
        '/System/Library/Fonts/AppleMyungjo.ttf'
    ]

    font_configured = False
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                # 폰트 추가
                fm.fontManager.addfont(font_path)

                # 폰트 이름 찾기
                prop = fm.FontProperties(fname=font_path)
                font_name = prop.get_name()

                # matplotlib 설정
                plt.rcParams['font.family'] = font_name
                plt.rcParams['axes.unicode_minus'] = False

                print(f"Korean font configured: {font_name} from {font_path}")
                font_configured = True
                break
            except Exception as e:
                print(f"Failed to load font from {font_path}: {e}")
                continue

    if not font_configured:
        # 폴백: DejaVu Sans 사용 (기본 폰트)
        print("Warning: Could not find Korean font. Using default font.")
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['axes.unicode_minus'] = False

elif platform.system() == 'Windows':  # Windows
    matplotlib.rcParams['font.family'] = 'Malgun Gothic'
    matplotlib.rcParams['axes.unicode_minus'] = False
else:  # Linux
    matplotlib.rcParams['font.family'] = 'NanumGothic'
    matplotlib.rcParams['axes.unicode_minus'] = False

matplotlib.rcParams['font.size'] = 10

# Seaborn 스타일 설정
sns.set_style("whitegrid")


class VisualizationGenerator:
    """시각화 생성 클래스"""

    def __init__(self, output_dir="generated"):
        """
        초기화

        Args:
            output_dir: 시각화 저장 디렉토리
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        print(f"Output directory: {self.output_dir}")

    def plot_top20_ngrams(self, df_path=None):
        """
        상위 20개 N-gram 빈도 막대그래프

        Args:
            df_path: N-gram 데이터프레임 경로
        """
        print("Generating Top 20 N-grams visualization...")

        # 주의: 실제 n-gram 분석이 수행되지 않음
        # date_ngram.json과 nbc_modeling.ipynb가 존재하지 않음
        print("Warning: No actual n-gram data available - showing placeholder")

        # 데이터가 없으므로 빈 그래프 표시
        top_ngrams = {
            "No data available": 0
        }

        # 시각화 - 데이터 없음 표시
        plt.figure(figsize=(10, 8))
        plt.text(0.5, 0.5, 'N-gram Data Not Available\n\nNo n-gram analysis has been performed.\nThe files date_ngram.json and nbc_modeling.ipynb\ndo not exist in this project.',
                ha='center', va='center', fontsize=16,
                transform=plt.gca().transAxes, color='red')
        plt.xlabel('', fontsize=12)
        plt.ylabel('', fontsize=12)
        plt.title('Top 20 N-grams by Frequency (Data Not Available)', fontsize=14, fontweight='bold')
        plt.xticks([])
        plt.yticks([])

        plt.tight_layout()
        output_path = self.output_dir / 'top20_ngrams.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Saved: {output_path}")

    def plot_performance_curve(self):
        """
        v1 → v4 성능 개선 곡선
        """
        print("Generating performance curve...")

        # 주의: 실제 모델링이 수행되지 않음 (nbc_modeling.ipynb 없음)
        # 아래는 예시 값임
        data = {
            'Version': ['v1\n(Not Available)', 'v2\n(Not Available)', 'v3\n(Not Available)', 'v4\n(Not Available)'],
            'F1-Score': [0, 0, 0, 0],
            'Improvement': [0, 0, 0, 0]
        }
        df_perf = pd.DataFrame(data)

        # 서브플롯 생성
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # 왼쪽: 성능 곡선 (데이터 없음)
        ax1.text(0.5, 0.5, 'Model Performance Data\nNot Available\n\nNo NBC model training performed',
                ha='center', va='center', fontsize=16,
                transform=ax1.transAxes, color='red')
        ax1.set_xlabel('Version', fontsize=12)
        ax1.set_ylabel('F1-Score (%)', fontsize=12)
        ax1.set_title('Model Performance Improvement (Data Not Available)', fontsize=14, fontweight='bold')
        ax1.set_xticks([])
        ax1.set_yticks([])
        ax1.grid(False)

        # 오른쪽: 개선율 막대그래프 (데이터 없음)
        ax2.text(0.5, 0.5, 'Improvement Data\nNot Available\n\nNo model comparison available',
                ha='center', va='center', fontsize=16,
                transform=ax2.transAxes, color='red')
        ax2.set_xlabel('Version', fontsize=12)
        ax2.set_ylabel('Improvement (%p)', fontsize=12)
        ax2.set_title('Incremental Improvements (Data Not Available)', fontsize=14, fontweight='bold')
        ax2.set_xticks([])
        ax2.set_yticks([])
        ax2.grid(False)

        plt.tight_layout()
        output_path = self.output_dir / 'performance_curve.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Saved: {output_path}")

    def plot_news_statistics(self):
        """
        뉴스 수집 통계 시각화 (월별 추이 + 언론사 비율)
        """
        print("Generating news statistics...")

        # 1. 실제 월별 수집량 데이터 (crawler/data/unified에서 추출)
        monthly_news_data = {
            "2014-01": 1464, "2014-02": 1419, "2014-03": 1589, "2014-04": 1388, "2014-05": 1378, "2014-06": 1520,
            "2014-07": 1938, "2014-08": 1842, "2014-09": 1891, "2014-10": 2060, "2014-11": 1791, "2014-12": 1903,
            "2015-01": 1984, "2015-02": 1788, "2015-03": 2787, "2015-04": 2242, "2015-05": 2268, "2015-06": 2590,
            "2015-07": 2172, "2015-08": 2350, "2015-09": 3506, "2015-10": 3197, "2015-11": 3487, "2015-12": 4184,
            "2016-01": 3121, "2016-02": 2929, "2016-03": 3183, "2016-04": 2583, "2016-05": 2658, "2016-06": 3031,
            "2016-07": 2478, "2016-08": 2821, "2016-09": 2950, "2016-10": 2682, "2016-11": 2900, "2016-12": 3316,
            "2017-01": 2569, "2017-02": 2469, "2017-03": 3247, "2017-04": 2149, "2017-05": 2007, "2017-06": 2550,
            "2017-07": 2404, "2017-08": 2078, "2017-09": 2289, "2017-10": 2201, "2017-11": 2377, "2017-12": 2245,
            "2018-01": 2196, "2018-02": 2441, "2018-03": 2390, "2018-04": 2231, "2018-05": 2396, "2018-06": 2293,
            "2018-07": 2250, "2018-08": 2116, "2018-09": 2005, "2018-10": 2883, "2018-11": 2287, "2018-12": 2333,
            "2019-01": 2243, "2019-02": 1502, "2019-03": 2105, "2019-04": 1841, "2019-05": 1806, "2019-06": 2212,
            "2019-07": 2800, "2019-08": 2579, "2019-09": 1756, "2019-10": 1866, "2019-11": 1474, "2019-12": 1403,
            "2020-01": 1405, "2020-02": 1772, "2020-03": 3385, "2020-04": 1774, "2020-05": 1578, "2020-06": 1723,
            "2020-07": 1611, "2020-08": 1631, "2020-09": 1758, "2020-10": 1492, "2020-11": 1550, "2020-12": 1455,
            "2021-01": 1936, "2021-02": 1882, "2021-03": 2960, "2021-04": 2157, "2021-05": 1949, "2021-06": 2519,
            "2021-07": 2323, "2021-08": 2111, "2021-09": 2077, "2021-10": 2298, "2021-11": 2548, "2021-12": 2342,
            "2022-01": 3134, "2022-02": 2626, "2022-03": 2941, "2022-04": 3319, "2022-05": 3312, "2022-06": 3899,
            "2022-07": 4262, "2022-08": 3515, "2022-09": 4029, "2022-10": 4078, "2022-11": 3923, "2022-12": 3658,
            "2023-01": 3695, "2023-02": 3500, "2023-03": 3763, "2023-04": 3049, "2023-05": 3051, "2023-06": 3287,
            "2023-07": 3005, "2023-08": 3324, "2023-09": 3013, "2023-10": 3746, "2023-11": 3683, "2023-12": 3378,
            "2024-01": 3696, "2024-02": 3223, "2024-03": 3282, "2024-04": 3637, "2024-05": 3330, "2024-06": 3044,
            "2024-07": 3738, "2024-08": 3734, "2024-09": 3287, "2024-10": 3228, "2024-11": 2961, "2024-12": 2957,
            "2025-01": 2836, "2025-02": 2513, "2025-03": 2326, "2025-04": 2540, "2025-05": 2394, "2025-06": 2363,
            "2025-07": 2593, "2025-08": 2540, "2025-09": 120,
        }

        # 날짜와 값을 분리
        dates = pd.to_datetime(list(monthly_news_data.keys()), format='%Y-%m')
        monthly_counts = list(monthly_news_data.values())

        # 2. 언론사별 데이터
        news_sources = {
            '인포맥스\n(177,406건)': 177406,
            '이데일리\n(112,201건)': 112201,
            '연합뉴스\n(69,544건)': 69544
        }

        # 서브플롯 생성
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # 왼쪽: 월별 수집량 추이
        ax1.plot(dates, monthly_counts, linewidth=2, color='#2E86AB')
        ax1.fill_between(dates, monthly_counts, alpha=0.3, color='#2E86AB')
        ax1.set_xlabel('Date', fontsize=12)
        ax1.set_ylabel('Number of Articles', fontsize=12)
        ax1.set_title('Monthly News Collection Trend', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)

        # x축 범위 명시적 제한 (2026년 제거)
        ax1.set_xlim([pd.Timestamp('2014-01-01'), pd.Timestamp('2025-09-30')])

        # 주요 이벤트 표시
        ax1.axvline(pd.Timestamp('2022-07-01'), color='red', linestyle='--', alpha=0.5)
        ax1.text(pd.Timestamp('2022-07-01'), ax1.get_ylim()[1]*0.9, '긴축 시작',
                ha='center', fontsize=9, color='red')

        # 오른쪽: 언론사별 비율 파이차트
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        explode = (0.05, 0, 0)  # 최대 비중 강조

        wedges, texts, autotexts = ax2.pie(news_sources.values(),
                                            labels=news_sources.keys(),
                                            colors=colors,
                                            explode=explode,
                                            autopct='%1.1f%%',
                                            startangle=90,
                                            textprops={'fontsize': 10, 'family': 'Apple SD Gothic Neo'})

        ax2.set_title('News Sources Distribution', fontsize=14, fontweight='bold')

        # 라벨 텍스트 폰트 설정
        for text in texts:
            text.set_fontfamily('Apple SD Gothic Neo')

        # 퍼센트 텍스트 굵게
        for autotext in autotexts:
            autotext.set_fontweight('bold')
            autotext.set_color('white')

        # 총 기사 수 표시
        total_articles = sum(news_sources.values())
        ax2.text(0, -1.3, f'Total: {total_articles:,} articles',
                ha='center', fontsize=11, fontweight='bold')

        plt.tight_layout()
        output_path = self.output_dir / 'news_statistics.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Saved: {output_path}")

    def plot_data_size_comparison(self):
        """
        전처리 전후 데이터 크기 비교
        """
        print("Generating data size comparison...")

        # 주의: nbc_modeling.ipynb가 실제로 존재하지 않음
        # 아래 값들은 추정치임
        print("Warning: No actual n-gram analysis performed - using estimates")
        initial_ngrams = 0    # 실제 데이터 없음
        filtered_ngrams = 0   # 실제 데이터 없음

        # 데이터 처리 단계 - 추정치 (실제 n-gram 분석이 수행되지 않음)
        stages = ['Raw News\n(359K docs)', 'Cleaned Text', 'All N-grams\n(Estimated)', 'Filtered N-grams\n(Not Available)']
        # 주의: 실제 n-gram 추출이 수행되지 않아 추정치 사용
        # 원본 뉴스 1.1GB → n-gram 추출시 약 70-100GB 예상
        sizes_gb = [1.1, 0.8, 75.0, 0.01]  # 추정치 (실제 데이터 없음, 0 대신 0.01 사용)
        colors = ['#FF6B6B', '#FFA07A', '#98D8C8', '#6BB6FF']

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # 왼쪽: 단계별 크기 변화 (로그 스케일)
        bars = ax1.bar(stages, sizes_gb, color=colors, edgecolor='black', linewidth=2)
        ax1.set_ylabel('Size (GB)', fontsize=12)
        ax1.set_title('Data Processing Pipeline', fontsize=14, fontweight='bold')
        ax1.set_yscale('log')  # 로그 스케일 사용
        ax1.grid(True, alpha=0.3, axis='y')

        # 값 표시
        for bar, size in zip(bars, sizes_gb):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.1,
                    f'{size:.1f} GB' if size >= 1 else f'{size*1000:.1f} MB',
                    ha='center', fontsize=10, fontweight='bold')

        # 오른쪽: N-gram 필터링 효과 (데이터 없음)
        # 실제 n-gram 분석이 수행되지 않아 표시할 수 없음
        ax2.text(0.5, 0.5, 'N-gram Analysis\nNot Performed\n\n(No date_ngram.json found)',
                ha='center', va='center', fontsize=16,
                transform=ax2.transAxes, color='red')
        ax2.set_xlabel('', fontsize=12)
        ax2.set_ylabel('', fontsize=12)
        ax2.set_title('N-gram Filtering Effect (Data Not Available)', fontsize=14, fontweight='bold')
        ax2.set_xticks([])
        ax2.set_yticks([])
        ax2.grid(False)

        plt.tight_layout()
        output_path = self.output_dir / 'data_size_comparison.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Saved: {output_path}")

    def plot_class_distribution(self):
        """
        Hawkish/Dovish 클래스 분포
        """
        print("Generating class distribution...")

        # 데이터
        train_data = {'Dovish': 439, 'Hawkish': 576}
        test_data = {'Dovish': 103, 'Hawkish': 151}

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # 색상
        colors = ['#4ECDC4', '#FF6B6B']

        # 왼쪽: Train 데이터
        wedges1, texts1, autotexts1 = ax1.pie(train_data.values(),
                                               labels=train_data.keys(),
                                               colors=colors,
                                               autopct='%1.1f%%',
                                               startangle=90)
        ax1.set_title('Train Set Distribution (n=1,015)', fontsize=12, fontweight='bold')

        # 오른쪽: Test 데이터
        wedges2, texts2, autotexts2 = ax2.pie(test_data.values(),
                                              labels=test_data.keys(),
                                              colors=colors,
                                              autopct='%1.1f%%',
                                              startangle=90)
        ax2.set_title('Test Set Distribution (n=254)', fontsize=12, fontweight='bold')

        # 스타일 조정
        for autotexts in [autotexts1, autotexts2]:
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')

        plt.suptitle('Class Distribution: Hawkish vs Dovish', fontsize=14, fontweight='bold')
        plt.tight_layout()

        output_path = self.output_dir / 'class_distribution.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Saved: {output_path}")

    def generate_all(self):
        """
        모든 시각화 생성
        """
        print("=" * 50)
        print("Generating All Visualizations")
        print("=" * 50)

        # 각 시각화 생성
        self.plot_top20_ngrams()
        self.plot_performance_curve()
        self.plot_news_statistics()
        self.plot_data_size_comparison()
        self.plot_class_distribution()

        print("\n" + "=" * 50)
        print(f"✅ All visualizations saved to {self.output_dir}")
        print("=" * 50)


def main():
    """메인 실행 함수"""
    # 시각화 생성기 인스턴스 생성
    generator = VisualizationGenerator()

    # 모든 시각화 생성
    generator.generate_all()

    # 생성된 파일 목록 출력
    print("\nGenerated files:")
    for file in generator.output_dir.glob("*.png"):
        size_kb = os.path.getsize(file) / 1024
        print(f"  - {file.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()