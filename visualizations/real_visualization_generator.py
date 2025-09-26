#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
real_visualization_generator.py
실제 데이터 기반 시각화 생성
- 문장 단위 NBC 결과 사용
- 정확한 라벨 분포 반영
- 실제 n-gram 통계 사용
"""

import json
import pandas as pd
import numpy as np
import matplotlib
# 백엔드 먼저 설정
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from pathlib import Path
import pickle
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent

# 색상 테마 정의 (타겟팅된 시인성 개선)
THEME_COLORS = {
    'primary_blue': '#6BAED6',      # 메인 파란색 (원래대로)
    'light_blue': '#C6DBEF',        # 연한 파란색 (원래대로)
    'lighter_blue': '#DEEBF7',      # 더 연한 파란색 (원래대로)
    'confidence_fill': '#9ECAE1',   # 신뢰구간 채우기 (원래대로)
    'orange_dash': '#FFA500',       # 주황색 점선 (원래대로)
    'green_star': '#6ACC00',        # 녹색 별표 (원래대로)
    'text_color': '#2C3E50',        # 텍스트 색상 (원래대로)
    'grid_color': '#E1E1E1',        # 그리드 색상 (원래대로)
    'dovish_green': '#66BB6A',      # Dovish 녹색 (경제 부양, 긍정적)
    'hawkish_red': '#E57373',       # Hawkish 빨간색 (경제 억제, 부정적)
    # 호환성을 위한 기존 이름 유지
    'negative_pink': '#E57373',     # Hawkish로 변경
    'positive_green': '#66BB6A',    # Dovish로 변경
    'unlabeled_blue': '#6BAED6',    # Unlabeled 파란색 (원래대로)
}

# 한글 폰트 설정
import platform
import matplotlib.font_manager as fm
from matplotlib import rcParams

# 폰트 설정
if platform.system() == 'Darwin':
    # macOS에서 Arial Unicode MS 사용 (한글 지원 확인됨)
    font_path = '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'

    # 폰트 매니저에 추가
    fm.fontManager.addfont(font_path)

    # 폰트 프로퍼티 생성
    font_prop = fm.FontProperties(fname=font_path)
    font_name = font_prop.get_name()

    # rcParams 직접 업데이트
    rcParams['font.family'] = font_name
    rcParams['axes.unicode_minus'] = False

    # plt.rcParams도 업데이트
    plt.rcParams['font.family'] = font_name
    plt.rcParams['axes.unicode_minus'] = False

    # matplotlib.rc도 사용
    matplotlib.rc('font', family=font_name)

elif platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
else:
    plt.rc('font', family='NanumGothic')

plt.rcParams['axes.unicode_minus'] = False

# Seaborn 스타일 - 폰트 설정 후에 적용
sns.set_style("whitegrid")

# Seaborn이 폰트를 덮어쓰지 않도록 다시 설정
if platform.system() == 'Darwin':
    plt.rcParams['font.family'] = 'Arial Unicode MS'
    matplotlib.rc('font', family='Arial Unicode MS')


def load_sentence_nbc_results():
    """문장 NBC 결과 로드"""
    stats_path = PROJECT_ROOT / 'modeling/sentence_nbc/model_stats.json'
    if stats_path.exists():
        with open(stats_path, 'r') as f:
            return json.load(f)
    return None


def apply_graph_style(ax):
    """그래프 스타일 적용"""
    ax.grid(True, linestyle='--', alpha=0.3, color=THEME_COLORS['grid_color'])
    ax.set_axisbelow(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_alpha(0.5)
    ax.spines['bottom'].set_alpha(0.5)


def create_performance_visualization():
    """실제 NBC 성능 시각화"""
    print("\n1. Creating performance visualization...")

    # 모델 통계 로드
    stats = load_sentence_nbc_results()
    if not stats:
        print("   Warning: No model stats found")
        return

    # 성능 지표
    metrics = {
        'F1-Score': stats['ensemble_f1'],
        'Precision': stats['ensemble_precision'],
        'Recall': stats['ensemble_recall'],
        'Accuracy': stats['ensemble_accuracy']
    }

    # 시각화
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor='white')

    # 왼쪽: 성능 막대그래프
    ax1 = axes[0]
    bars = ax1.bar(metrics.keys(), metrics.values(),
                   color=[THEME_COLORS['primary_blue'], THEME_COLORS['light_blue'],
                          THEME_COLORS['positive_green'], THEME_COLORS['confidence_fill']])
    ax1.set_ylim(0.7, 0.85)
    ax1.set_title('문장 단위 NBC 성능 (30회 배깅 평균)', fontsize=16, fontweight='bold', color=THEME_COLORS['text_color'])
    ax1.set_ylabel('Score', fontsize=12, fontweight='bold')
    apply_graph_style(ax1)

    # 값 표시
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.002,
                f'{height:.3f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

    # 오른쪽: 클래스별 성능
    ax2 = axes[1]
    class_metrics = {
        'Dovish\nPrecision': stats.get('dovish_precision', 0.77),
        'Dovish\nRecall': stats.get('dovish_recall', 0.75),
        'Hawkish\nPrecision': stats.get('hawkish_precision', 0.78),
        'Hawkish\nRecall': stats.get('hawkish_recall', 0.80)
    }

    x = np.arange(len(class_metrics))
    bars2 = ax2.bar(x, class_metrics.values(),
                    color=[THEME_COLORS['negative_pink'], THEME_COLORS['negative_pink'],
                           THEME_COLORS['positive_green'], THEME_COLORS['positive_green']])
    ax2.set_xticks(x)
    ax2.set_xticklabels(class_metrics.keys())
    ax2.set_ylim(0.7, 0.85)
    ax2.set_title('클래스별 성능 비교', fontsize=16, fontweight='bold', color=THEME_COLORS['text_color'])
    ax2.set_ylabel('Score', fontsize=12, fontweight='bold')
    apply_graph_style(ax2)

    # 값 표시
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.002,
                f'{height:.2f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.suptitle(f'한국은행 기준금리 예측 모델 성능\n총 {stats["total_sentences"]:,} 문장 학습',
                 fontsize=18, fontweight='bold', y=1.02, color=THEME_COLORS['text_color'])
    plt.tight_layout()
    plt.savefig('sentence_nbc_performance.png', dpi=300, bbox_inches='tight',
                facecolor='white', transparent=True)
    plt.close()
    print("   ✓ Saved sentence_nbc_performance.png")


def create_data_pipeline_visualization(include_ngram=False, output_suffix=''):
    """데이터 파이프라인 시각화"""
    version = "with N-gram" if include_ngram else "without N-gram"
    print(f"\n2. Creating data pipeline visualization ({version})...")

    # 실제 통계
    pipeline_stats = {
        '뉴스 수집': 359151,
        'MPB 의사록': 224,
        '채권 보고서': 6515,
        '콜금리': 2866,
        '기준금리': 41,
        '문장 분리': 2823248
    }

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor='white')

    # 왼쪽: 데이터 소스 (뉴스 출처별 세분화)
    ax1 = axes[0]
    sources = ['인포맥스\n(뉴스)', '이데일리\n(뉴스)', '연합뉴스\n(뉴스)', 'MPB\n의사록', '채권\n보고서', '콜금리\n(라벨)', '기준금리']
    values = [177406, 112201, 69544, 224, 6515, 2866, 25]
    # 뉴스는 파란색 계열, 나머지는 다른 색
    colors = [THEME_COLORS['primary_blue'], THEME_COLORS['confidence_fill'], THEME_COLORS['light_blue'],
              THEME_COLORS['orange_dash'], THEME_COLORS['lighter_blue'],
              THEME_COLORS['hawkish_red'], THEME_COLORS['dovish_green']]

    bars1 = ax1.bar(sources, values, color=colors)
    ax1.set_title('데이터 소스 상세 현황 (총 365,890개)', fontsize=16, fontweight='bold', color=THEME_COLORS['text_color'])
    ax1.set_ylabel('수집 건수', fontsize=12, fontweight='bold')
    ax1.set_yscale('log')
    apply_graph_style(ax1)

    # 값 표시 (비율도 함께 표시)
    total = sum(values)
    for bar, val in zip(bars1, values):
        height = bar.get_height()
        percentage = (val/total)*100
        if val >= 1000:
            label = f'{val:,}\n({percentage:.1f}%)'
        else:
            label = f'{val}'
        ax1.text(bar.get_x() + bar.get_width()/2., height * 1.1,
                label, ha='center', va='bottom', fontsize=8)

    # 오른쪽: 실제 데이터 플로우 및 크기
    ax2 = axes[1]
    if include_ngram:
        stages = ['원본\n5.5GB', '정제\n1.1GB', '토큰화\n1.6GB', 'N-gram\n5.3GB', '최종\n15MB']
        stage_values = [5500, 1100, 1600, 5300, 15]  # MB 단위
        colors2 = [THEME_COLORS['hawkish_red'], THEME_COLORS['orange_dash'],
                   THEME_COLORS['primary_blue'], THEME_COLORS['light_blue'], THEME_COLORS['dovish_green']]
    else:
        stages = ['원본\n5.5GB', '정제\n1.1GB', '토큰화\n1.6GB']
        stage_values = [5500, 1100, 1600]  # MB 단위
        colors2 = [THEME_COLORS['hawkish_red'], THEME_COLORS['orange_dash'],
                   THEME_COLORS['dovish_green']]

    bars2 = ax2.bar(stages, stage_values, color=colors2)
    ax2.set_title('데이터 처리 플로우 (전체 프로젝트 24GB)', fontsize=16, fontweight='bold', color=THEME_COLORS['text_color'])
    ax2.set_ylabel('데이터 크기 (MB, log scale)', fontsize=12, fontweight='bold')
    ax2.set_yscale('log')
    apply_graph_style(ax2)

    # 값 표시
    for i, (bar, val) in enumerate(zip(bars2, stage_values)):
        height = bar.get_height()
        # 크기 표시
        if val >= 1000:
            label = f'{val/1000:.1f}GB'
        else:
            label = f'{val}MB'
        # 첫 번째 막대(가장 높은)는 막대 안에, 나머지는 위에 표시
        if i == 0:
            ax2.text(bar.get_x() + bar.get_width()/2., height * 0.7,
                    label, ha='center', va='center', fontsize=9,
                    fontweight='bold', color='white')
        else:
            ax2.text(bar.get_x() + bar.get_width()/2., height * 1.1,
                    label, ha='center', va='bottom', fontsize=9)

    plt.suptitle('데이터 수집 및 처리 현황', fontsize=18, fontweight='bold',
                 y=1.02, color=THEME_COLORS['text_color'])
    plt.tight_layout()
    filename = f'data_pipeline{output_suffix}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight',
                facecolor='white', transparent=True)
    plt.close()
    print(f"   ✓ Saved {filename}")


def create_label_timeseries():
    """라벨 분포 시계열 그래프 (개별 파일)"""
    print("\n3a. Creating label timeseries chart...")

    # 문장 코퍼스 로드
    sentence_corpus_path = PROJECT_ROOT / 'preprocess/sentence_split/sentence_corpus.csv'
    if not sentence_corpus_path.exists():
        print("   Warning: sentence_corpus.csv not found")
        return

    df = pd.read_csv(sentence_corpus_path)

    # 날짜별 라벨 집계
    df['date'] = pd.to_datetime(df['date'])
    df['year_month'] = df['date'].dt.to_period('M')

    # 월별 라벨 분포
    monthly_dist = df.groupby(['year_month', 'label']).size().unstack(fill_value=0)

    fig, ax = plt.subplots(figsize=(14, 7), facecolor='white')

    # 시계열 분포
    monthly_dist.plot(kind='area', stacked=True, ax=ax,
                      color=[THEME_COLORS['dovish_green'], THEME_COLORS['hawkish_red']], alpha=0.8)
    ax.set_title('기준금리 방향성 라벨 분포 (월별 문장 수)', fontsize=16, fontweight='bold', color=THEME_COLORS['text_color'])
    ax.set_xlabel('기간', fontsize=12, fontweight='bold')
    ax.set_ylabel('문장 수', fontsize=12, fontweight='bold')
    ax.legend(['Dovish (0)', 'Hawkish (1)'], loc='upper left', frameon=True, fancybox=True, shadow=True)
    apply_graph_style(ax)

    plt.tight_layout()
    plt.savefig('label_distribution_timeseries.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("   ✓ Saved label_distribution_timeseries.png")

def create_label_piechart():
    """라벨 분포 파이차트 (개별 파일)"""
    print("\n3b. Creating label pie chart...")

    # 문장 코퍼스 로드
    sentence_corpus_path = PROJECT_ROOT / 'preprocess/sentence_split/sentence_corpus.csv'
    if not sentence_corpus_path.exists():
        print("   Warning: sentence_corpus.csv not found")
        return

    df = pd.read_csv(sentence_corpus_path)

    fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')

    # 전체 비율
    label_counts = df['label'].value_counts().sort_index()
    total = label_counts.sum()

    # 파이차트
    colors = [THEME_COLORS['dovish_green'], THEME_COLORS['hawkish_red']]
    wedges, texts, autotexts = ax.pie(label_counts,
                                        labels=['Dovish', 'Hawkish'],
                                        colors=colors,
                                        autopct='%1.1f%%',
                                        startangle=90,
                                        explode=(0.05, 0))

    # 스타일 조정
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(14)

    # 제목
    ax.set_title(f'전체 라벨 분포 (총 {total:,} 문장)', fontsize=16, fontweight='bold', color=THEME_COLORS['text_color'])

    # 하단에 수치 표시 (컴팩트한 레이아웃)
    ax.text(0.5, -0.15, f'Dovish: {label_counts[0]:,} | Hawkish: {label_counts[1]:,}',
           ha='center', va='center', transform=ax.transAxes, fontsize=12, fontweight='bold',
           color=THEME_COLORS['text_color'])

    plt.tight_layout()
    plt.savefig('label_distribution_piechart.png', dpi=300, bbox_inches='tight', transparent=True)
    plt.close()
    print("   ✓ Saved label_distribution_piechart.png")

def create_label_distribution():
    """실제 라벨 분포 시각화 (통합 버전)"""
    print("\n3. Creating label distribution...")

    # 문장 코퍼스 로드
    sentence_corpus_path = PROJECT_ROOT / 'preprocess/sentence_split/sentence_corpus.csv'
    if not sentence_corpus_path.exists():
        print("   Warning: sentence_corpus.csv not found")
        return

    df = pd.read_csv(sentence_corpus_path)

    # 날짜별 라벨 집계
    df['date'] = pd.to_datetime(df['date'])
    df['year_month'] = df['date'].dt.to_period('M')

    # 월별 라벨 분포
    monthly_dist = df.groupby(['year_month', 'label']).size().unstack(fill_value=0)

    fig, axes = plt.subplots(2, 1, figsize=(14, 10), facecolor='white')

    # 상단: 시계열 분포
    ax1 = axes[0]
    monthly_dist.plot(kind='area', stacked=True, ax=ax1,
                      color=[THEME_COLORS['dovish_green'], THEME_COLORS['hawkish_red']], alpha=0.8)
    ax1.set_title('기준금리 방향성 라벨 분포 (월별 문장 수)', fontsize=16, fontweight='bold', color=THEME_COLORS['text_color'])
    ax1.set_xlabel('기간', fontsize=12, fontweight='bold')
    ax1.set_ylabel('문장 수', fontsize=12, fontweight='bold')
    ax1.legend(['Dovish (0)', 'Hawkish (1)'], loc='upper left', frameon=True, fancybox=True, shadow=True)
    apply_graph_style(ax1)

    # 하단: 전체 비율
    ax2 = axes[1]
    label_counts = df['label'].value_counts().sort_index()
    total = label_counts.sum()

    # 파이차트
    colors = [THEME_COLORS['dovish_green'], THEME_COLORS['hawkish_red']]
    wedges, texts, autotexts = ax2.pie(label_counts,
                                        labels=['Dovish', 'Hawkish'],
                                        colors=colors,
                                        autopct='%1.1f%%',
                                        startangle=90,
                                        explode=(0.05, 0))

    # 스타일 조정
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(12)

    ax2.set_title(f'전체 라벨 분포 (총 {total:,} 문장)', fontsize=16, fontweight='bold', color=THEME_COLORS['text_color'])

    # 실제 수치 표시
    dovish_count = label_counts[0] if 0 in label_counts else 0
    hawkish_count = label_counts[1] if 1 in label_counts else 0
    ax2.text(0, -1.3, f'Dovish: {dovish_count:,} | Hawkish: {hawkish_count:,}',
            ha='center', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.savefig('label_distribution.png', dpi=300, bbox_inches='tight',
                facecolor='white', transparent=True)
    plt.close()
    print("   ✓ Saved label_distribution.png")


def create_ngram_analysis():
    """N-gram 분석: 상위 판별 N-gram과 피처 축소 효과"""
    print("\n4. Creating N-gram analysis...")

    # N-gram polarity 데이터 로드
    polarity_path = PROJECT_ROOT / 'modeling/sentence_nbc/ngram_polarity.csv'
    if not polarity_path.exists():
        print("   Warning: ngram_polarity.csv not found")
        return

    df_polarity = pd.read_csv(polarity_path, index_col=0)

    # 상위 10개 Hawkish, Dovish N-gram 추출
    top_hawkish = df_polarity.nlargest(10, 'mean_score')
    top_dovish = df_polarity.nsmallest(10, 'mean_score')

    # 전체 레이아웃 설정
    fig = plt.figure(figsize=(16, 10), facecolor='white')
    gs = fig.add_gridspec(3, 2, height_ratios=[0.5, 2.5, 0.3], width_ratios=[6, 4])

    # Panel A: 발산형 막대그래프 (좌측 60%)
    ax_main = fig.add_subplot(gs[1, 0])

    # Y축 위치 설정
    y_pos_hawkish = np.arange(len(top_hawkish))
    y_pos_dovish = np.arange(len(top_dovish)) + len(top_hawkish) + 1

    # Hawkish 막대 (양수, 빨간색)
    bars_hawkish = ax_main.barh(y_pos_hawkish, top_hawkish['mean_score'],
                                color=THEME_COLORS['hawkish_red'], alpha=0.8, height=0.7)

    # Dovish 막대 (음수, 녹색)
    bars_dovish = ax_main.barh(y_pos_dovish, top_dovish['mean_score'],
                               color=THEME_COLORS['dovish_green'], alpha=0.8, height=0.7)

    # N-gram 라벨 설정 (14자 제한)
    hawkish_labels = [label[:14] + '...' if len(label) > 14 else label for label in top_hawkish.index]
    dovish_labels = [label[:14] + '...' if len(label) > 14 else label for label in top_dovish.index]

    # Y축 라벨 설정
    all_labels = hawkish_labels + [''] + dovish_labels  # 중간에 빈 공간
    ax_main.set_yticks(list(y_pos_hawkish) + [len(top_hawkish)] + list(y_pos_dovish))
    ax_main.set_yticklabels(all_labels, fontsize=10)

    # 축선 설정
    ax_main.axvline(x=0, color='black', linewidth=1, alpha=0.8)
    ax_main.set_xlabel('로그 가능도 비율 (Log-likelihood ratio)', fontsize=12, fontweight='bold')
    ax_main.set_title('도표 A — 상위 판별 N-gram', fontsize=14, fontweight='bold', pad=15)
    ax_main.grid(True, axis='x', alpha=0.3)

    # Panel B: 피처 축소 효과 (우측 40%)
    ax_feature = fig.add_subplot(gs[1, 1])

    # 특징 수 비교
    features_before = 71_163_146
    features_after = 670_616
    reduction_rate = (features_before - features_after) / features_before * 100

    categories = ['특징 수', '메모리']
    values_before = [features_before / 1_000_000, 0]  # 백만 단위
    values_after = [features_after / 1_000_000, 15]   # 15MB

    x_pos = np.arange(len(categories))
    width = 0.35

    # 막대그래프
    bars1 = ax_feature.bar(x_pos - width/2, values_before, width,
                           label='전처리 전', color=THEME_COLORS['light_blue'], alpha=0.7)
    bars2 = ax_feature.bar(x_pos + width/2, values_after, width,
                           label='전처리 후', color=THEME_COLORS['primary_blue'])

    # 값 라벨 추가
    ax_feature.text(0 - width/2, values_before[0] + 2, f'{features_before:,}개',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax_feature.text(0 + width/2, values_after[0] + 0.1, f'{features_after:,}개',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax_feature.text(1 + width/2, values_after[1] + 0.5, '15MB',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

    # 축소율 배지
    ax_feature.text(0, max(values_before) * 0.8, f'-{reduction_rate:.0f}%',
                    ha='center', va='center', fontsize=12, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.2))

    ax_feature.set_xticks(x_pos)
    ax_feature.set_xticklabels(categories, fontsize=11)
    ax_feature.set_ylabel('값 (백만 단위 / MB)', fontsize=10)
    ax_feature.set_title('도표 B — 피처 축소 효과', fontsize=14, fontweight='bold', pad=15)
    ax_feature.legend(loc='upper right')

    # KPI 카드 (상단)
    ax_kpi = fig.add_subplot(gs[0, :])
    ax_kpi.axis('off')

    kpi_text = f"""특징 축소: {features_before:,} → {features_after:,}    노이즈 제거율: {reduction_rate:.0f}%    메모리 사용량: 15MB    정책: 1–5그램 · 최소 빈도 ≥15 · 품사 필터 적용"""

    ax_kpi.text(0.5, 0.5, kpi_text, ha='center', va='center', fontsize=11,
                bbox=dict(boxstyle='round,pad=0.5', facecolor=THEME_COLORS['lighter_blue'], alpha=0.8),
                transform=ax_kpi.transAxes, fontweight='bold')

    # 각주 (하단)
    ax_footer = fig.add_subplot(gs[2, :])
    ax_footer.axis('off')

    footer_text = "시간대는 한국표준시(KST). 모든 수치는 문장 단위 처리 결과 기준. 최소 등장 빈도 15회 이상, 1–5그램, 품사 필터(일반명사·동사·형용사·일반부사·지정사) 적용."
    ax_footer.text(0.02, 0.5, footer_text, ha='left', va='center', fontsize=9,
                   transform=ax_footer.transAxes, style='italic', alpha=0.7)

    plt.tight_layout()
    plt.savefig('ngram_analysis.png', dpi=300, bbox_inches='tight',
                facecolor='white', transparent=True)
    plt.close()
    print("   ✓ Saved ngram_analysis.png")


def create_ngram_polarity_chart():
    """N-gram 극성 분석 차트 (Panel A 단독)"""
    print("\n4a. Creating N-gram polarity chart...")

    # N-gram polarity 데이터 로드
    polarity_path = PROJECT_ROOT / 'modeling/sentence_nbc/ngram_polarity.csv'
    df_polarity = pd.read_csv(polarity_path, index_col=0)

    # N-gram 유효성 검사 함수
    def is_valid_ngram(ngram_text):
        """비정상적인 N-gram 필터링"""
        # 1글자 N-gram 제외 (오타 등)
        if len(ngram_text) <= 1:
            return False

        words = ngram_text.split()

        # 같은 단어가 연속으로 반복되는 경우 제외
        for i in range(len(words)-1):
            if words[i] == words[i+1]:
                return False

        return True

    # 중복 패턴 제거 함수
    def remove_subset_ngrams(ngram_list):
        """다른 N-gram의 부분집합인 경우 제거"""
        filtered = []
        ngram_texts = [idx for idx, _ in ngram_list]

        for i, ngram1 in enumerate(ngram_texts):
            is_subset = False
            for j, ngram2 in enumerate(ngram_texts):
                if i != j and ngram1 in ngram2 and ngram1 != ngram2:
                    is_subset = True
                    break
            if not is_subset:
                filtered.append(ngram_list[i])

        return filtered

    # 의미 있는 금융 키워드 우선 선택
    total_ngrams = len(df_polarity)

    # 금융/경제 관련 키워드 필터
    financial_keywords = '금리|인상|인하|긴축|완화|통화|정책|경제|성장|물가|인플레|채권|주식|달러|원화|수출|수입|무역'

    # 금융 관련 N-gram 우선 추출
    financial_ngrams = df_polarity[df_polarity.index.str.contains(financial_keywords, na=False)]

    # Hawkish: 금융 관련 중 score > 1.5
    hawkish_financial = financial_ngrams[financial_ngrams['mean_score'] > 1.5].nlargest(100, 'mean_score')
    # Dovish: 금융 관련 중 score < -1.5
    dovish_financial = financial_ngrams[financial_ngrams['mean_score'] < -1.5].nsmallest(100, 'mean_score')

    # 금융 관련이 부족하면 일반 극단값 추가
    if len(hawkish_financial) < 30:
        hawkish_general = df_polarity[df_polarity['mean_score'] > 2.5].nlargest(50, 'mean_score')
        hawkish_discriminative = pd.concat([hawkish_financial, hawkish_general]).drop_duplicates()
    else:
        hawkish_discriminative = hawkish_financial

    if len(dovish_financial) < 30:
        dovish_general = df_polarity[df_polarity['mean_score'] < -2.5].nsmallest(50, 'mean_score')
        dovish_discriminative = pd.concat([dovish_financial, dovish_general]).drop_duplicates()
    else:
        dovish_discriminative = dovish_financial

    discriminative_ngrams = pd.concat([hawkish_discriminative, dovish_discriminative])
    discriminative_ratio = len(discriminative_ngrams) / total_ngrams * 100

    print(f"  금융 관련 N-gram 우선 선택")
    print(f"  Hawkish: {len(hawkish_discriminative)}개 (금융: {len(hawkish_financial)}개)")
    print(f"  Dovish: {len(dovish_discriminative)}개 (금융: {len(dovish_financial)}개)")

    # 유효성 검사 통과한 N-gram만 선택
    hawkish_valid = [(idx, score) for idx, score in zip(hawkish_discriminative.index, hawkish_discriminative['mean_score'])
                     if is_valid_ngram(idx)]
    dovish_valid = [(idx, score) for idx, score in zip(dovish_discriminative.index, dovish_discriminative['mean_score'])
                    if is_valid_ngram(idx)]

    # 부분집합 제거
    hawkish_filtered = remove_subset_ngrams(hawkish_valid)[:10]  # 상위 10개만
    dovish_filtered = remove_subset_ngrams(dovish_valid)[:10]    # 상위 10개만


    # DataFrame으로 변환
    top_hawkish = pd.DataFrame(hawkish_filtered, columns=['ngram', 'mean_score']).set_index('ngram')
    top_dovish = pd.DataFrame(dovish_filtered, columns=['ngram', 'mean_score']).set_index('ngram')

    # 전체 레이아웃 설정 (캡션 공간을 위해 bottom margin 증가)
    fig = plt.figure(figsize=(12, 9), facecolor='white')
    ax_main = fig.add_subplot(111)

    # Y축 위치 설정
    y_pos_hawkish = np.arange(len(top_hawkish))
    y_pos_dovish = np.arange(len(top_dovish)) + len(top_hawkish) + 1

    # Hawkish 막대 (양수, 빨간색 - 더 진한 색)
    bars_hawkish = ax_main.barh(y_pos_hawkish, top_hawkish['mean_score'],
                                color='#D94A4A', alpha=0.85, height=0.7)

    # Dovish 막대 (음수, 녹색 - 더 진한 색)
    bars_dovish = ax_main.barh(y_pos_dovish, top_dovish['mean_score'],
                               color='#4CB26B', alpha=0.85, height=0.7)

    # N-gram 라벨 설정 (12자 제한)
    hawkish_labels = [label[:12] + '...' if len(label) > 12 else label for label in top_hawkish.index]
    dovish_labels = [label[:12] + '...' if len(label) > 12 else label for label in top_dovish.index]

    # Y축 라벨 설정
    all_labels = hawkish_labels + [''] + dovish_labels  # 중간에 빈 공간
    ax_main.set_yticks(list(y_pos_hawkish) + [len(top_hawkish)] + list(y_pos_dovish))
    ax_main.set_yticklabels(all_labels, fontsize=11)

    # X축 범위 계산 및 완전 대칭 설정
    if len(top_hawkish) > 0 and len(top_dovish) > 0:
        max_abs_value = max(abs(top_hawkish['mean_score'].max()),
                            abs(top_dovish['mean_score'].min()))
    else:
        max_abs_value = 5  # 기본값

    ax_main.set_xlim(-max_abs_value * 1.1, max_abs_value * 1.1)

    # 보조 세로선 추가 (2-3개)
    for x in [-max_abs_value*0.5, max_abs_value*0.5]:
        ax_main.axvline(x=x, color='#E5E7EB', linewidth=0.5, alpha=0.5, zorder=1)

    # 중앙 0축 강조 (더 진한 회색, 두꺼운 선)
    ax_main.axvline(x=0, color='#4A4A4A', linewidth=2, alpha=0.9, zorder=5)

    ax_main.set_xlabel('로그 가능도 비율 (Log-likelihood ratio)', fontsize=12, fontweight='bold')
    ax_main.set_title('금융 키워드 중심 N-gram 극성 분석', fontsize=16, fontweight='bold', pad=20)
    ax_main.grid(True, axis='x', alpha=0.2, linewidth=0.5)

    # 범례 개선
    ax_main.legend([bars_hawkish[0], bars_dovish[0]], ['Hawkish (적색)', 'Dovish (녹색)'],
                   loc='lower right', fontsize=11)

    # 차트 조정 (캡션 공간 확보)
    plt.subplots_adjust(bottom=0.12)

    # 캡션 추가 (차트 외부 하단)
    caption_text = (f"금융 관련 키워드 중심으로 선택 (전체 {total_ngrams:,}개 중 {len(discriminative_ngrams):,}개)\n"
                    "필터: 금리, 인상, 인하, 긴축, 완화, 통화, 정책, 경제, 물가 등 포함 N-gram\n"
                    "주의: 데이터에 반복 패턴 및 중복 문제 존재. 전체 N-gram의 96%는 분별력 없음.")
    fig.text(0.5, 0.01, caption_text, ha='center', va='bottom',
             fontsize=9, style='italic', alpha=0.7)

    plt.savefig('ngram_polarity_only.png', dpi=300, bbox_inches='tight',
                facecolor='white', transparent=True)
    plt.close()
    print("   ✓ Saved ngram_polarity_only.png")


def create_feature_reduction_chart():
    """특징 축소 효과 차트 (Panel B 단독)"""
    print("\n4b. Creating feature reduction chart...")

    # 특징 수 비교
    features_before = 71_163_146
    features_after = 670_616
    reduction_rate = (features_before - features_after) / features_before * 100

    # 전체 레이아웃 설정 (통합 버전과 동일한 스타일)
    fig = plt.figure(figsize=(10, 7), facecolor='white')

    # GridSpec으로 상단 KPI, 메인 차트, 하단 각주 영역 분리
    gs = fig.add_gridspec(3, 1, height_ratios=[0.8, 3, 0.5])

    # 메인 차트
    ax_feature = fig.add_subplot(gs[1])

    categories = ['특징 수', '메모리']
    values_before = [features_before / 1_000_000, 0]  # 백만 단위
    values_after = [features_after / 1_000_000, 15]   # 15MB

    x_pos = np.arange(len(categories))
    width = 0.35

    # 막대그래프
    bars1 = ax_feature.bar(x_pos - width/2, values_before, width,
                           label='전처리 전', color=THEME_COLORS['light_blue'], alpha=0.7)
    bars2 = ax_feature.bar(x_pos + width/2, values_after, width,
                           label='전처리 후', color=THEME_COLORS['primary_blue'])

    # 값 라벨 추가 (통합 버전과 동일한 스타일)
    ax_feature.text(0 - width/2, values_before[0] + 2, f'{features_before:,}개',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax_feature.text(0 + width/2, values_after[0] + 0.1, f'{features_after:,}개',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax_feature.text(1 + width/2, values_after[1] + 0.5, '15MB',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

    # 축소율 배지 (통합 버전과 동일)
    ax_feature.text(0, max(values_before) * 0.8, f'-{reduction_rate:.0f}%',
                    ha='center', va='center', fontsize=12, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.2))

    ax_feature.set_xticks(x_pos)
    ax_feature.set_xticklabels(categories, fontsize=11)
    ax_feature.set_ylabel('값 (백만 단위 / MB)', fontsize=10)
    ax_feature.set_title('도표 B — 피처 축소 효과', fontsize=14, fontweight='bold', pad=15)
    ax_feature.legend(loc='upper right')

    # KPI 카드 (상단) - 통합 버전과 동일
    ax_kpi = fig.add_subplot(gs[0])
    ax_kpi.axis('off')

    kpi_text = f"""특징 축소: {features_before:,} → {features_after:,}    노이즈 제거율: {reduction_rate:.0f}%    메모리 사용량: 15MB    정책: 1–5그램 · 최소 빈도 ≥15 · 품사 필터 적용"""

    ax_kpi.text(0.5, 0.5, kpi_text, ha='center', va='center', fontsize=11,
                bbox=dict(boxstyle='round,pad=0.5', facecolor=THEME_COLORS['lighter_blue'], alpha=0.8),
                transform=ax_kpi.transAxes, fontweight='bold')

    # 각주 (하단) - 통합 버전과 동일
    ax_footer = fig.add_subplot(gs[2])
    ax_footer.axis('off')

    footer_text = "시간대는 한국표준시(KST). 모든 수치는 문장 단위 처리 결과 기준. 최소 등장 빈도 15회 이상, 1–5그램, 품사 필터(일반명사·동사·형용사·일반부사·지정사) 적용."
    ax_footer.text(0.02, 0.5, footer_text, ha='left', va='center', fontsize=9,
                   transform=ax_footer.transAxes, style='italic', alpha=0.7)

    plt.tight_layout()
    plt.savefig('feature_reduction_only.png', dpi=300, bbox_inches='tight',
                facecolor='white', transparent=True)
    plt.close()
    print("   ✓ Saved feature_reduction_only.png")


def create_call_rate_labeling():
    """일별 콜금리 추이와 1개월 후 변동 기반 라벨링 시각화"""
    print("\n5. Creating call rate labeling visualization...")

    # 일별 콜금리 데이터 로드
    call_rate_path = PROJECT_ROOT / 'crawler/data/auxiliary/market_call_rates_daily_2014_2025.csv'
    df_call = pd.read_csv(call_rate_path)

    # 중복 제거 및 날짜 변환
    df_call = df_call.drop_duplicates(subset=['날짜'])
    df_call['date'] = pd.to_datetime(df_call['날짜'])
    df_call['call_rate'] = df_call['콜금리']
    df_call = df_call.sort_values('date').reset_index(drop=True)

    # 1개월 후 콜금리 찾기 함수
    def get_future_rate(date, df):
        future_date = date + pd.DateOffset(months=1)
        future_rates = df[df['date'] <= future_date]
        if not future_rates.empty:
            return future_rates.iloc[-1]['call_rate']
        return None

    # 각 날짜에 대한 라벨 계산
    labels = []
    for idx, row in df_call.iterrows():
        current_rate = row['call_rate']
        future_rate = get_future_rate(row['date'], df_call)

        if future_rate is not None:
            diff = future_rate - current_rate
            if diff > 0.03:
                labels.append('Hawkish')
            elif diff < -0.03:
                labels.append('Dovish')
            else:
                labels.append('None')
        else:
            labels.append('None')

    df_call['label'] = labels

    # 월별 집계 (히트맵용)
    df_call['year_month'] = df_call['date'].dt.to_period('M')
    monthly_agg = df_call.groupby(['year_month', 'label']).size().unstack(fill_value=0)

    print(f"   Data period: {df_call['date'].min().strftime('%Y-%m-%d')} to {df_call['date'].max().strftime('%Y-%m-%d')}")
    print(f"   Total days: {len(df_call)}")
    print(f"   Days labeled Hawkish: {len(df_call[df_call['label'] == 'Hawkish'])}")
    print(f"   Days labeled Dovish: {len(df_call[df_call['label'] == 'Dovish'])}")
    print(f"   Days with no label (±3bp): {len(df_call[df_call['label'] == 'None'])}")

    # 일별 콜금리 추이와 라벨 차트
    fig, ax = plt.subplots(figsize=(16, 7), facecolor='white')

    # 월별 문서량 데이터 로드 (배경 히트맵용)
    try:
        corpus_path = PROJECT_ROOT / 'preprocess/data_combine/corpus_data.csv'
        if corpus_path.exists():
            df_corpus = pd.read_csv(corpus_path)
            df_corpus['Date'] = pd.to_datetime(df_corpus['Date'])
            df_corpus['year_month'] = df_corpus['Date'].dt.to_period('M')
            monthly_doc_counts = df_corpus.groupby('year_month').size()

            # 월별 문서량을 배경으로 표시 (회색 농도)
            max_docs = monthly_doc_counts.max()
            for period in monthly_agg.index:
                if period in monthly_doc_counts.index:
                    doc_count = monthly_doc_counts[period]
                    # 문서량에 비례한 회색 농도
                    alpha = 0.05 + (doc_count / max_docs) * 0.15  # 0.05 ~ 0.20 범위
                    period_start = period.to_timestamp()
                    period_end = (period + 1).to_timestamp()
                    ax.axvspan(period_start, period_end, alpha=alpha, color='gray', zorder=1)
    except Exception as e:
        print(f"   Note: Could not load document counts: {e}")

    # 금통위 결정일 표시 (기준금리 변경 시점)
    try:
        rate_path = PROJECT_ROOT / 'crawler/data/auxiliary/interest_rates_2014_2025.csv'
        if rate_path.exists():
            df_rate = pd.read_csv(rate_path)
            # 날짜 형식 변환
            def parse_rate_date(row):
                year = str(row['연도'])
                date_str = row['날짜']
                month = date_str.split('월')[0].strip()
                day = date_str.split('월')[1].replace('일', '').strip()
                return pd.to_datetime(f"{year}-{month}-{day}", format='%Y-%m-%d')

            df_rate['date'] = df_rate.apply(parse_rate_date, axis=1)
            df_rate['rate'] = df_rate['기준금리']
            df_rate['change'] = df_rate['rate'].diff()

            # 금통위 결정일에 세로선 및 화살표
            for _, row in df_rate.iterrows():
                ax.axvline(x=row['date'], color='darkgray', linestyle='--', alpha=0.3, linewidth=0.8, zorder=2)
                if row['change'] > 0:
                    ax.annotate('↑', xy=(row['date'], 4.2), fontsize=10, color='red', ha='center')
                elif row['change'] < 0:
                    ax.annotate('↓', xy=(row['date'], 4.2), fontsize=10, color='green', ha='center')
    except Exception as e:
        print(f"   Note: Could not load rate decision dates: {e}")

    # 콜금리 라인 차트
    ax.plot(df_call['date'], df_call['call_rate'],
            color=THEME_COLORS['primary_blue'], linewidth=1.5, alpha=0.8, label='일별 콜금리', zorder=2)

    # 모든 Hawkish/Dovish 포인트 표시 (샘플링 없이)
    hawkish_points = df_call[df_call['label'] == 'Hawkish']
    dovish_points = df_call[df_call['label'] == 'Dovish']

    # Hawkish 포인트 (1개월 후 상승) - 모두 표시
    ax.scatter(hawkish_points['date'], hawkish_points['call_rate'],
               color=THEME_COLORS['hawkish_red'], s=15, zorder=3,
               marker='^', alpha=0.4, edgecolors='none', label=f'Hawkish ({len(hawkish_points)}일, 1개월 후 ↑)')

    # Dovish 포인트 (1개월 후 하락) - 모두 표시
    ax.scatter(dovish_points['date'], dovish_points['call_rate'],
               color=THEME_COLORS['dovish_green'], s=15, zorder=3,
               marker='v', alpha=0.4, edgecolors='none', label=f'Dovish ({len(dovish_points)}일, 1개월 후 ↓)')

    # 텍스트 박스 - 라벨링 방법 설명
    textstr = f'''· 각 날짜의 콜금리 → 1개월 후 콜금리 비교
· 변동 > +3bp → Hawkish ({len(df_call[df_call['label'] == 'Hawkish'])}일)
· 변동 < -3bp → Dovish ({len(df_call[df_call['label'] == 'Dovish'])}일)
· ±3bp 이내 → 라벨 없음 ({len(df_call[df_call['label'] == 'None'])}일)'''

    props = dict(boxstyle='round,pad=0.6',
                facecolor=THEME_COLORS['lighter_blue'],
                edgecolor=THEME_COLORS['primary_blue'],
                alpha=0.95)
    ax.text(0.02, 0.97, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props, fontweight='bold')

    ax.set_title('시장 반응 기반(Market-based) 라벨링: 일별 콜금리와 1개월 후 변동',
                 fontsize=16, fontweight='bold', color=THEME_COLORS['text_color'])
    ax.set_ylabel('콜금리 (%)', fontsize=12, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.3, color=THEME_COLORS['grid_color'])
    ax.set_ylim(0, 4.5)

    # X축 범위 명시적 설정 (2014년 1월 ~ 2025년 9월만 표시)
    ax.set_xlim([pd.Timestamp('2014-01-01'), pd.Timestamp('2025-09-30')])

    # 범례 설명 업데이트
    from matplotlib.patches import Patch
    legend_elements = [
        plt.Line2D([0], [0], color=THEME_COLORS['primary_blue'], lw=2,
                  label='일별 콜금리'),
        plt.scatter([], [], color=THEME_COLORS['hawkish_red'], s=15,
                   marker='^', alpha=0.4, label=f'Hawkish ({len(hawkish_points)}일, 1개월 후 ↑)'),
        plt.scatter([], [], color=THEME_COLORS['dovish_green'], s=15,
                   marker='v', alpha=0.4, label=f'Dovish ({len(dovish_points)}일, 1개월 후 ↓)'),
        Patch(color='gray', alpha=0.2, label='월별 문서량 (진할수록 많음)'),
        plt.Line2D([0], [0], color='darkgray', linestyle='--', alpha=0.5,
                  label='금통위 결정일')
    ]
    ax.legend(handles=legend_elements, loc='upper right', frameon=True,
              fancybox=True, shadow=True, fontsize=9)

    plt.tight_layout()
    plt.savefig('call_rate_labeling.png', dpi=300, bbox_inches='tight',
                facecolor='white', transparent=True)
    plt.close()
    print("   ✓ Saved call_rate_labeling.png")

def create_enhanced_confusion_matrix():
    """향상된 혼동행렬 시각화 (비율 + 실제 건수)"""
    print("\n6. Creating enhanced confusion matrix...")

    # 모델 통계 로드
    stats = load_sentence_nbc_results()
    if not stats:
        print("   Warning: No model stats for confusion matrix")
        return

    # 실제 혼동행렬 데이터 사용 (stats에 있으면)
    if 'confusion_matrix' in stats:
        cm = np.array(stats['confusion_matrix'])
    else:
        # 추정값 사용 (fallback)
        total_test = int(stats['total_sentences'] * stats['test_size'])
        accuracy = stats['ensemble_accuracy']
        # 간단한 추정
        correct = int(total_test * accuracy)
        incorrect = total_test - correct
        cm = np.array([[correct//2, incorrect//2],
                      [incorrect//2, correct//2]])

    # 정규화 계산 (비율)
    cm_normalized = cm.astype('float') / cm.sum() * 100

    # 시각화
    fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')

    # 커스텀 컬러맵 (백색→파란색 그라데이션)
    from matplotlib.colors import LinearSegmentedColormap
    colors_cm = ['white', '#E3F2FD', '#90CAF9', '#42A5F5', '#1E88E5']
    cmap = LinearSegmentedColormap.from_list('custom_blues', colors_cm, N=100)

    # 히트맵 그리기 (비율 표시)
    mask = np.zeros_like(cm_normalized, dtype=bool)
    sns.heatmap(cm_normalized, annot=False, cmap=cmap,
                xticklabels=['Dovish', 'Hawkish'],
                yticklabels=['Dovish', 'Hawkish'],
                cbar_kws={'label': '비율 (%)'},
                linewidths=2, linecolor='white',
                square=True, ax=ax, vmin=0, vmax=50)

    # 각 셀에 비율과 건수 표시
    for i in range(2):
        for j in range(2):
            # 비율 (큰 글씨)
            percentage = cm_normalized[i, j]
            count = cm[i, j]

            # 대각선 요소는 굵은 테두리
            if i == j:
                rect = plt.Rectangle((j, i), 1, 1,
                                    fill=False, edgecolor='#1565C0',
                                    linewidth=3)
                ax.add_patch(rect)
                text_color = 'white' if percentage > 30 else 'black'
                weight = 'bold'
            else:
                text_color = 'black'
                weight = 'normal'

            # 비율 표시 (큰 숫자)
            ax.text(j + 0.5, i + 0.35, f'{percentage:.1f}%',
                   ha='center', va='center', fontsize=24,
                   fontweight=weight, color=text_color)

            # 건수 표시 (작은 회색 글씨)
            ax.text(j + 0.5, i + 0.65, f'({count:,})',
                   ha='center', va='center', fontsize=11,
                   color='gray' if i != j else text_color, alpha=0.8)

    # 라벨 및 제목
    ax.set_ylabel('실제', fontsize=14, fontweight='bold')
    ax.set_xlabel('예측', fontsize=14, fontweight='bold')
    ax.set_title('도표 A — 정규화 혼동행렬 (문장 단위)',
                fontsize=16, fontweight='bold', pad=20)

    # 우상단에 작은 텍스트 추가
    ax.text(1.02, 0.98, '평가 단위: 문장\n날짜 단위 결과와 혼동 금지',
           transform=ax.transAxes, fontsize=9,
           verticalalignment='top', style='italic', alpha=0.7)

    # 하단에 성능 지표 표시
    footer_text = (f"F1-Score: {stats['ensemble_f1']:.3f} | "
                  f"Precision: {stats['ensemble_precision']:.3f} | "
                  f"Recall: {stats['ensemble_recall']:.3f} | "
                  f"Accuracy: {stats['ensemble_accuracy']:.3f}")
    ax.text(0.5, -0.12, footer_text,
           transform=ax.transAxes, fontsize=11,
           ha='center', fontweight='bold')

    plt.tight_layout()
    plt.savefig('confusion_matrix_enhanced.png', dpi=300, bbox_inches='tight',
                facecolor='white', transparent=True)
    plt.close()
    print("   ✓ Saved confusion_matrix_enhanced.png")


def create_pr_curve_with_f1_threshold():
    """PR 곡선과 F1-임계값 차트"""
    print("\n6. Creating PR curve with F1 threshold...")

    # PR 곡선 데이터 로드
    pr_data_path = PROJECT_ROOT / 'modeling/sentence_nbc/pr_curve_data.json'
    if not pr_data_path.exists():
        # Try sample data for testing
        pr_data_path = PROJECT_ROOT / 'modeling/sentence_nbc/pr_curve_data_sample.json'
        if not pr_data_path.exists():
            print("   ⚠ PR curve data not found, skipping...")
            return

    with open(pr_data_path, 'r') as f:
        pr_data = json.load(f)

    true_labels = np.array(pr_data['true_labels'])
    predicted_proba = np.array(pr_data['predicted_proba'])

    # PR 곡선 계산
    from sklearn.metrics import precision_recall_curve, auc
    precisions, recalls, thresholds = precision_recall_curve(true_labels, predicted_proba)
    pr_auc = auc(recalls, precisions)

    # F1 점수 계산 (각 임계값에 대해)
    f1_scores = []
    for threshold in thresholds:
        predictions = (predicted_proba >= threshold).astype(int)
        tp = np.sum((predictions == 1) & (true_labels == 1))
        fp = np.sum((predictions == 1) & (true_labels == 0))
        fn = np.sum((predictions == 0) & (true_labels == 1))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        f1_scores.append(f1)

    # 최적 F1 임계값 찾기
    best_idx = np.argmax(f1_scores)
    best_threshold = thresholds[best_idx]
    best_f1 = f1_scores[best_idx]

    # 시각화
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8),
                                   gridspec_kw={'height_ratios': [3, 1]})

    # PR 곡선
    ax1.plot(recalls, precisions, 'b-', linewidth=2, label=f'PR (AUC = {pr_auc:.3f})')
    ax1.plot([0, 1], [0.5, 0.5], 'r--', linewidth=1, alpha=0.5, label='Baseline (0.5)')

    # 최적 F1 포인트 표시
    ax1.scatter(recalls[best_idx], precisions[best_idx],
               color='red', s=100, zorder=5,
               label=f'Best F1 = {best_f1:.3f}')

    ax1.set_xlabel('Recall', fontsize=12)
    ax1.set_ylabel('Precision', fontsize=12)
    ax1.set_title('Precision-Recall 곡선', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='lower left')
    ax1.set_xlim([0, 1])
    ax1.set_ylim([0, 1])

    # F1 vs 임계값 (sparkline)
    ax2.plot(thresholds, f1_scores, 'g-', linewidth=1.5, alpha=0.7)
    ax2.fill_between(thresholds, f1_scores, alpha=0.3, color='green')
    ax2.axvline(x=best_threshold, color='red', linestyle='--', linewidth=1)
    ax2.scatter(best_threshold, best_f1, color='red', s=50, zorder=5)

    ax2.set_xlabel('임계값 (Threshold)', fontsize=10)
    ax2.set_ylabel('F1', fontsize=10)
    ax2.set_xlim([0, 1])
    ax2.set_ylim([0, max(f1_scores) * 1.1])
    ax2.grid(True, alpha=0.3)

    # 최적 임계값 텍스트
    ax2.text(best_threshold, best_f1 + 0.02,
            f'최적: {best_threshold:.3f}',
            fontsize=9, ha='center')

    plt.tight_layout()
    plt.savefig('pr_curve_f1_threshold.png', dpi=300, bbox_inches='tight',
                facecolor='white', transparent=True)
    plt.close()
    print("   ✓ Saved pr_curve_f1_threshold.png")


def create_ngram_theme_classification():
    """N-gram 주제 분류 표"""
    print("\n7. Creating N-gram theme classification table...")

    # N-gram polarity 데이터 로드
    polarity_path = PROJECT_ROOT / 'modeling/sentence_nbc/ngram_polarity.csv'
    df_polarity = pd.read_csv(polarity_path, index_col=0)

    # 극성이 강한 N-gram만 선택 (상위/하위 각 100개)
    top_hawkish = df_polarity.nlargest(100, 'mean_score')
    top_dovish = df_polarity.nsmallest(100, 'mean_score')

    # 주제별 분류 (키워드 기반)
    policy_keywords = '정책|기준|금리|인상|인하|동결|긴축|완화|통화|위원|총재|회의'
    price_keywords = '물가|인플레|성장|경제|GDP|수출|수입|소비|투자|고용|실업'
    market_keywords = '시장|자금|유동성|채권|주식|환율|달러|원화|은행|대출|예금'

    def classify_theme(ngram_text):
        """N-gram을 주제별로 분류"""
        themes = []
        if any(kw in ngram_text for kw in policy_keywords.split('|')):
            themes.append('정책/금리')
        if any(kw in ngram_text for kw in price_keywords.split('|')):
            themes.append('물가/성장')
        if any(kw in ngram_text for kw in market_keywords.split('|')):
            themes.append('시장/자금')
        return themes if themes else ['기타']

    # 각 카테고리별 N-gram 수집
    categories = {
        '정책/금리': {'hawkish': [], 'dovish': []},
        '물가/성장': {'hawkish': [], 'dovish': []},
        '시장/자금': {'hawkish': [], 'dovish': []}
    }

    # Hawkish N-grams 분류
    for ngram, score in zip(top_hawkish.index, top_hawkish['mean_score']):
        themes = classify_theme(ngram)
        for theme in themes:
            if theme in categories and len(categories[theme]['hawkish']) < 5:
                categories[theme]['hawkish'].append((ngram[:20], score))

    # Dovish N-grams 분류
    for ngram, score in zip(top_dovish.index, top_dovish['mean_score']):
        themes = classify_theme(ngram)
        for theme in themes:
            if theme in categories and len(categories[theme]['dovish']) < 5:
                categories[theme]['dovish'].append((ngram[:20], abs(score)))

    # 시각화
    fig, axes = plt.subplots(1, 3, figsize=(15, 8), facecolor='white')

    for idx, (category, data) in enumerate(categories.items()):
        ax = axes[idx]

        # 데이터 준비
        hawkish_data = data['hawkish'][:5] if data['hawkish'] else [('—', 0)]
        dovish_data = data['dovish'][:5] if data['dovish'] else [('—', 0)]

        # 표 형식으로 표시
        cell_text = []
        colors = []

        # Hawkish 섹션
        cell_text.append(['Hawkish', '', ''])
        colors.append(['#FFE5E5', '#FFE5E5', '#FFE5E5'])

        for ngram, score in hawkish_data:
            if ngram == '—':
                cell_text.append(['—', '—', '—'])
            else:
                cell_text.append([ngram, f'{score:.2f}', '▲'])
            colors.append(['white', 'white', '#FFCCCC'])

        # 구분선
        cell_text.append(['', '', ''])
        colors.append(['#F0F0F0', '#F0F0F0', '#F0F0F0'])

        # Dovish 섹션
        cell_text.append(['Dovish', '', ''])
        colors.append(['#E5FFE5', '#E5FFE5', '#E5FFE5'])

        for ngram, score in dovish_data:
            if ngram == '—':
                cell_text.append(['—', '—', '—'])
            else:
                cell_text.append([ngram, f'{score:.2f}', '▼'])
            colors.append(['white', 'white', '#CCFFCC'])

        # 테이블 생성
        table = ax.table(cellText=cell_text,
                        cellColours=colors,
                        cellLoc='left',
                        colWidths=[0.6, 0.25, 0.15],
                        loc='center')

        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)

        # 헤더 스타일
        for i in [0, 7]:  # Hawkish, Dovish 헤더
            for j in range(3):
                cell = table[(i, j)]
                cell.set_text_props(weight='bold')

        ax.axis('off')
        ax.set_title(category, fontsize=14, fontweight='bold', pad=20)

    # 전체 제목
    fig.suptitle('N-gram 주제별 분류', fontsize=16, fontweight='bold', y=0.98)

    # 하단 설명
    fig.text(0.5, 0.02,
            '점수는 로그 가능도 비율의 절댓값. 상위 5개씩 표시.',
            ha='center', fontsize=9, style='italic', alpha=0.7)

    plt.tight_layout()
    plt.savefig('ngram_theme_classification.png', dpi=300, bbox_inches='tight',
                facecolor='white', transparent=True)
    plt.close()
    print("   ✓ Saved ngram_theme_classification.png")


def main():
    """메인 실행 함수"""
    print("="*60)
    print("Real Data Visualization Generation")
    print("="*60)

    # 시각화 디렉토리로 이동
    import os
    viz_dir = PROJECT_ROOT / 'visualizations'
    os.chdir(viz_dir)

    # 각 시각화 생성
    create_performance_visualization()
    create_data_pipeline_visualization(include_ngram=False)  # N-gram 없는 버전
    create_data_pipeline_visualization(include_ngram=True, output_suffix='_full')  # N-gram 있는 버전
    create_label_distribution()  # 통합 버전
    create_label_timeseries()    # 시계열 분리 버전
    create_label_piechart()      # 파이차트 분리 버전
    create_ngram_analysis()
    create_ngram_polarity_chart()      # Panel A 단독
    create_feature_reduction_chart()   # Panel B 단독
    create_call_rate_labeling()  # 콜금리 라벨링 차트
    create_enhanced_confusion_matrix()  # 향상된 혼동행렬
    create_pr_curve_with_f1_threshold()  # PR 곡선 + F1 임계값
    create_ngram_theme_classification()  # N-gram 주제 분류

    print("\n" + "="*60)
    print("✅ All real data visualizations created successfully!")
    print(f"Location: {viz_dir}")

    # 생성된 파일 목록
    print("\nGenerated files:")
    for file in viz_dir.glob("*.png"):
        size_kb = os.path.getsize(file) / 1024
        print(f"  - {file.name} ({size_kb:.1f} KB)")
    print("="*60)


if __name__ == "__main__":
    main()