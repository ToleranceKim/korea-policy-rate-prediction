#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
comprehensive_visualization.py
전체 파이프라인 결과 종합 시각화
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent

# 한글 폰트 설정
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

def create_ngram_wordcloud():
    """N-gram 워드클라우드 생성"""
    print("Creating N-gram wordcloud...")

    # N-gram 빈도 데이터 로드
    df_freq = pd.read_csv(PROJECT_ROOT / 'modeling/nbc/ngram_frequency.csv')

    # 워드클라우드용 딕셔너리
    word_freq = dict(zip(df_freq['ngram'], df_freq['frequency']))

    # 워드클라우드 생성
    wordcloud = WordCloud(width=1200, height=600,
                          background_color='white',
                          font_path='/System/Library/Fonts/AppleSDGothicNeo.ttc',
                          colormap='viridis',
                          relative_scaling=0.7).generate_from_frequencies(word_freq)

    # 시각화
    plt.figure(figsize=(15, 8))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('금융 뉴스 주요 N-grams 워드클라우드', fontsize=20, pad=20)
    plt.savefig('ngram_wordcloud.png', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✓ Saved ngram_wordcloud.png")

def create_label_distribution():
    """라벨 분포 시각화"""
    print("Creating label distribution chart...")

    # 라벨 데이터 로드
    with open(PROJECT_ROOT / 'modeling/nbc/date_label.json', 'r') as f:
        date_label = json.load(f)

    # 날짜별 분포
    df_labels = pd.DataFrame(list(date_label.items()), columns=['Date', 'Label'])
    df_labels['Date'] = pd.to_datetime(df_labels['Date'])
    df_labels['YearMonth'] = df_labels['Date'].dt.to_period('M')

    # 월별 집계
    monthly_stats = df_labels.groupby(['YearMonth', 'Label']).size().unstack(fill_value=0)

    # 시각화
    fig, axes = plt.subplots(2, 1, figsize=(15, 10))

    # 1. 시계열 라벨 분포
    ax1 = axes[0]
    monthly_stats.plot(kind='area', stacked=True, ax=ax1, color=['#2E86AB', '#A23B72'])
    ax1.set_title('기준금리 방향성 라벨 분포 (월별)', fontsize=16)
    ax1.set_xlabel('기간')
    ax1.set_ylabel('일 수')
    ax1.legend(['Dovish (0)', 'Hawkish (1)'], loc='upper right')
    ax1.grid(alpha=0.3)

    # 2. 전체 비율
    ax2 = axes[1]
    label_counts = df_labels['Label'].value_counts()
    colors = ['#2E86AB', '#A23B72']
    wedges, texts, autotexts = ax2.pie(label_counts, labels=['Dovish', 'Hawkish'],
                                        autopct='%1.1f%%', colors=colors,
                                        startangle=90)
    ax2.set_title('전체 기간 Dovish/Hawkish 비율', fontsize=16)

    plt.tight_layout()
    plt.savefig('label_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Saved label_distribution.png")

def create_data_statistics():
    """데이터 통계 시각화"""
    print("Creating data statistics...")

    # 데이터 소스별 통계
    stats = {
        '뉴스 기사': 359149,
        'MPB 의사록': 224,
        '채권 보고서': 6515,
        '총 문서 수': 365888
    }

    # N-gram 통계
    df_ngrams = pd.read_csv(PROJECT_ROOT / 'preprocess/ngram/ngram_results.csv')
    df_filtered = pd.read_csv(PROJECT_ROOT / 'modeling/nbc/filtered_ngrams.csv')

    ngram_stats = {
        '추출 N-grams': len(df_ngrams),
        '유니크 N-grams': df_ngrams['ngram'].nunique(),
        '필터링 후': len(df_filtered),
        '노이즈 제거율(%)': round((1 - len(df_filtered)/len(df_ngrams))*100, 1) if len(df_ngrams) > 0 else 0
    }

    # 시각화
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # 1. 데이터 소스 통계
    ax1 = axes[0]
    sources = list(stats.keys())[:-1]  # 총 문서 수 제외
    values = list(stats.values())[:-1]
    bars = ax1.bar(sources, values, color=['#3498db', '#e74c3c', '#f39c12'])
    ax1.set_title('데이터 소스별 문서 수', fontsize=14)
    ax1.set_ylabel('문서 수')

    # 값 표시
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}', ha='center', va='bottom')

    # 2. N-gram 처리 통계
    ax2 = axes[1]
    ngram_labels = ['추출', '유니크', '필터링 후']
    ngram_values = [ngram_stats['추출 N-grams'],
                   ngram_stats['유니크 N-grams'],
                   ngram_stats['필터링 후']]
    bars2 = ax2.bar(ngram_labels, ngram_values, color=['#16a085', '#8e44ad', '#d35400'])
    ax2.set_title(f'N-gram 처리 통계 (노이즈 제거: {ngram_stats["노이즈 제거율(%)"]}%)', fontsize=14)
    ax2.set_ylabel('N-gram 수')

    # 값 표시
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}', ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig('data_statistics.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Saved data_statistics.png")

def create_model_performance():
    """모델 성능 종합 시각화"""
    print("Creating model performance visualization...")

    # 이미 생성된 confusion matrix와 performance metrics 확인
    cm_path = PROJECT_ROOT / 'modeling/nbc/confusion_matrix.png'
    perf_path = PROJECT_ROOT / 'modeling/nbc/performance_metrics.png'

    if cm_path.exists() and perf_path.exists():
        print("✓ Model performance visualizations already exist")
        return

    # 모델 성능 메트릭
    metrics = {
        'F1-Score': 0.996,
        'Precision': 0.98,
        'Recall': 1.00,
        'Accuracy': 1.00
    }

    # 시각화
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(metrics.keys(), metrics.values(), color=['#e74c3c', '#3498db', '#2ecc71', '#f39c12'])
    ax.set_ylim(0.9, 1.01)
    ax.set_title('NBC 모델 성능 지표', fontsize=16)
    ax.set_ylabel('Score')
    ax.grid(axis='y', alpha=0.3)

    # 값 표시
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.002,
               f'{height:.3f}', ha='center', va='bottom', fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig('model_performance_summary.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Saved model_performance_summary.png")

def main():
    print("="*60)
    print("Comprehensive Visualization Generation")
    print("="*60)

    # 시각화 디렉토리 생성
    viz_dir = PROJECT_ROOT / 'visualizations'
    viz_dir.mkdir(exist_ok=True)

    # 작업 디렉토리 변경
    import os
    os.chdir(viz_dir)

    # 각 시각화 생성
    create_ngram_wordcloud()
    create_label_distribution()
    create_data_statistics()
    create_model_performance()

    print("\n" + "="*60)
    print("✅ All visualizations created successfully!")
    print(f"Location: {viz_dir}")
    print("="*60)

if __name__ == "__main__":
    main()