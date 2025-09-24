#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pipeline_diagram_matplotlib.py
matplotlib을 사용한 전문적인 데이터 수집 파이프라인 다이어그램
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import matplotlib.lines as mlines
import numpy as np
from pathlib import Path

# 한글 폰트 설정
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

def create_pipeline_diagram():
    """전문적인 데이터 수집 파이프라인 다이어그램 생성"""

    fig, ax = plt.subplots(figsize=(16, 12), facecolor='white')
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis('off')

    # 색상 팔레트 (기존 시각화 테마와 통일)
    colors = {
        'primary': '#6BAED6',      # 메인 파란색
        'secondary': '#C6DBEF',    # 연한 파란색
        'accent1': '#66BB6A',      # 녹색 강조
        'accent2': '#E57373',      # 빨간색 강조
        'text': '#2C3E50',         # 텍스트
        'light': '#DEEBF7',        # 배경색
        'border': '#9ECAE1'        # 테두리
    }

    # 제목
    title = plt.text(8, 11.5, '한국은행 기준금리 예측 프로젝트\n데이터 수집 파이프라인',
                     fontsize=18, fontweight='bold', ha='center', va='top', color=colors['text'])

    # ===== 1. 데이터 소스 레이어 (최상단) =====
    y_source = 9.5

    # 뉴스 소스 박스
    news_sources = [
        ('연합뉴스', '69,544개', 2),
        ('이데일리', '112,201개', 5),
        ('인포맥스', '177,406개', 8)
    ]

    for name, count, x in news_sources:
        # 메인 박스
        box = FancyBboxPatch((x-0.8, y_source-0.4), 1.6, 0.8,
                             boxstyle='round,pad=0.05',
                             facecolor=colors['light'],
                             edgecolor=colors['primary'], linewidth=1.5)
        ax.add_patch(box)
        # 텍스트
        ax.text(x, y_source+0.1, name, fontsize=10, fontweight='bold',
                ha='center', va='center', color=colors['text'])
        ax.text(x, y_source-0.15, count, fontsize=9, ha='center', va='center',
                color=colors['text'])

    # 기타 데이터 소스
    other_sources = [
        ('MPB 의사록', '224개 PDF', 10.5),
        ('콜금리', '2,866개', 12),
        ('기준금리', '41개', 13.5),
        ('채권 리포트', '6,515개', 15)
    ]

    for name, count, x in other_sources:
        box = FancyBboxPatch((x-0.8, y_source-0.4), 1.6, 0.8,
                             boxstyle='round,pad=0.05',
                             facecolor=colors['secondary'], alpha=0.3,
                             edgecolor=colors['border'], linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, y_source+0.1, name, fontsize=10, fontweight='bold',
                ha='center', va='center', color=colors['text'])
        ax.text(x, y_source-0.15, count, fontsize=9, ha='center', va='center',
                color=colors['text'])

    # 소스 그룹 라벨
    ax.text(5, y_source+0.7, '뉴스 데이터 (359,151개)', fontsize=11,
            fontweight='bold', ha='center', color=colors['text'])
    ax.text(13, y_source+0.7, '보조 데이터', fontsize=11,
            fontweight='bold', ha='center', color=colors['text'])

    # ===== 2. 수집 방법 레이어 =====
    y_method = 7.5

    # 수집 방법 박스
    methods = [
        ('API 호출\n(JSON)', 2),
        ('웹페이지\n크롤링', 5),
        ('웹페이지\n크롤링', 8),
        ('PDF 다운로드\n→텍스트 추출', 10.5),
        ('한은 사이트\nJS 파싱', 12),
        ('대한상공회의소\n테이블 추출', 13.5),
        ('네이버 금융\n페이지 크롤링', 15)
    ]

    for text, x in methods:
        # 타원형 박스
        ellipse = mpatches.Ellipse((x, y_method), width=1.8, height=0.8,
                                   facecolor='white',
                                   edgecolor=colors['border'], linewidth=1)
        ax.add_patch(ellipse)
        ax.text(x, y_method, text, fontsize=9, ha='center', va='center', color=colors['text'])

    # ===== 3. 처리 방식 레이어 =====
    y_pool = 5.5

    # 순차 처리 (뉴스)
    seq_box = FancyBboxPatch((3, y_pool-0.4), 3, 0.8,
                             boxstyle='round,pad=0.05',
                             facecolor='white',
                             edgecolor=colors['primary'], linewidth=1.5)
    ax.add_patch(seq_box)
    ax.text(4.5, y_pool+0.1, '순차 처리', fontsize=10, fontweight='bold',
            ha='center', va='center', color=colors['text'])
    ax.text(4.5, y_pool-0.15, '뉴스 크롤링', fontsize=9,
            ha='center', va='center', color=colors['text'])

    # ThreadPoolExecutor (채권 전용)
    pool_box = FancyBboxPatch((10, y_pool-0.4), 3, 0.8,
                              boxstyle='round,pad=0.05',
                              facecolor=colors['light'], alpha=0.8,
                              edgecolor=colors['accent2'], linewidth=2)
    ax.add_patch(pool_box)
    ax.text(11.5, y_pool+0.1, '병렬 처리', fontsize=10, fontweight='bold',
            ha='center', va='center', color=colors['text'])
    ax.text(11.5, y_pool-0.15, '채권 페이지별 동시 수집\n(5 workers)', fontsize=9,
            ha='center', va='center', color=colors['text'])

    # ===== 4. 전처리 파이프라인 레이어 =====
    y_process = 3.5

    processes = [
        ('실패시 재시도\n3회 (2초 간격)', 3),
        ('중복 제거\nURL+제목 기준\n(228개, 0.06%)', 6),
        ('노이즈 제거\n기자명, 이메일,\n특수문자 (34.6%)', 9),
        ('품질 검증\n수집 성공률\n99.8%', 12)
    ]

    for text, x in processes:
        box = FancyBboxPatch((x-1.0, y_process-0.5), 2.0, 1.0,
                             boxstyle='round,pad=0.03',
                             facecolor='white',
                             edgecolor=colors['border'], linewidth=1)
        ax.add_patch(box)
        ax.text(x, y_process, text, fontsize=8.5, ha='center', va='center', color=colors['text'])

    # 전처리 그룹 박스
    process_group = FancyBboxPatch((1.5, y_process-0.7), 12, 1.4,
                                   boxstyle='round,pad=0.05',
                                   facecolor='none', edgecolor=colors['border'],
                                   linewidth=1, linestyle='--', alpha=0.5)
    ax.add_patch(process_group)
    ax.text(1.8, y_process+0.6, '전처리 파이프라인', fontsize=10, color=colors['text'])

    # ===== 5. 토큰화 레이어 =====
    y_token = 2

    token_box = FancyBboxPatch((6, y_token-0.4), 4, 0.8,
                               boxstyle='round,pad=0.05',
                               facecolor=colors['secondary'], alpha=0.3,
                               edgecolor=colors['primary'], linewidth=1.5)
    ax.add_patch(token_box)
    ax.text(8, y_token+0.1, '형태소 분석 (eKoNLPy + Mecab)', fontsize=10, fontweight='bold',
            ha='center', va='center', color=colors['text'])
    ax.text(8, y_token-0.15, '품사 태깅 후 명사/동사 추출 | 13GB→2.8GB', fontsize=9,
            ha='center', va='center', color=colors['text'])

    # ===== 6. 저장 레이어 =====
    y_db = 0.5

    # PostgreSQL 실린더 모양
    db_rect = FancyBboxPatch((6.5, y_db-0.3), 3, 0.6,
                             boxstyle='round,pad=0.03',
                             facecolor=colors['accent1'], alpha=0.2,
                             edgecolor=colors['accent1'], linewidth=2)
    ax.add_patch(db_rect)
    db_ellipse = mpatches.Ellipse((8, y_db+0.3), width=3, height=0.3,
                                  facecolor=colors['accent1'], alpha=0.2,
                                  edgecolor=colors['accent1'], linewidth=2)
    ax.add_patch(db_ellipse)
    ax.text(8, y_db, '데이터베이스 저장', fontsize=10, fontweight='bold',
            ha='center', va='center', color=colors['text'])
    ax.text(8, y_db-0.2, 'PostgreSQL (JSON 형식) | 85개 필드', fontsize=9,
            ha='center', va='center', color=colors['text'])

    # ===== 화살표 연결 =====
    # 소스 → 수집방법
    arrow_props = dict(arrowstyle='->', connectionstyle='arc3', lw=1,
                      color=colors['border'], alpha=0.5)

    # 뉴스 연결
    ax.annotate('', xy=(2, y_method+0.4), xytext=(2, y_source-0.5), arrowprops=arrow_props)
    ax.annotate('', xy=(5, y_method+0.4), xytext=(5, y_source-0.5), arrowprops=arrow_props)
    ax.annotate('', xy=(8, y_method+0.4), xytext=(8, y_source-0.5), arrowprops=arrow_props)

    # 기타 소스 연결
    ax.annotate('', xy=(11, y_method+0.4), xytext=(11, y_source-0.5), arrowprops=arrow_props)
    ax.annotate('', xy=(13, y_method+0.4), xytext=(13, y_source-0.5), arrowprops=arrow_props)
    ax.annotate('', xy=(15, y_method+0.4), xytext=(15, y_source-0.5), arrowprops=arrow_props)

    # 뉴스 수집방법 → 순차 처리
    for x in [2, 5, 8]:
        ax.annotate('', xy=(4.5, y_pool+0.4), xytext=(x, y_method-0.4),
                   arrowprops=dict(arrowstyle='->', lw=1, color=colors['primary'], alpha=0.4))

    # 보조 데이터 → 순차 처리 (MPB, 금리)
    for x in [10.5, 12, 13.5]:
        ax.annotate('', xy=(4.5, y_pool+0.4), xytext=(x, y_method-0.4),
                   arrowprops=dict(arrowstyle='->', lw=1, color=colors['border'], alpha=0.4))

    # 채권 → ThreadPool
    ax.annotate('', xy=(11.5, y_pool+0.4), xytext=(15, y_method-0.4),
               arrowprops=dict(arrowstyle='->', lw=1.5, color=colors['accent2'], alpha=0.6))

    # 처리 방식 → 전처리 (메인 플로우)
    main_arrow = dict(arrowstyle='->', lw=2, color=colors['text'], alpha=0.6)
    # 순차 처리 → 전처리
    ax.annotate('', xy=(6, y_process+0.5), xytext=(4.5, y_pool-0.5), arrowprops=main_arrow)
    # ThreadPool → 전처리
    ax.annotate('', xy=(9, y_process+0.5), xytext=(11.5, y_pool-0.5), arrowprops=main_arrow)
    # 전처리 → 토큰화 → DB
    ax.annotate('', xy=(8, y_token+0.5), xytext=(9, y_process-0.5), arrowprops=main_arrow)
    ax.annotate('', xy=(8, y_db+0.6), xytext=(8, y_token-0.5), arrowprops=main_arrow)

    # 전처리 내부 연결
    for i in range(3):
        x1, x2 = 3 + i*3, 6 + i*3
        ax.annotate('', xy=(x2, y_process), xytext=(x1+0.8, y_process),
                   arrowprops=dict(arrowstyle='->', lw=1, color=colors['accent1'], alpha=0.5))

    # ===== 통계 정보 박스 =====
    stats_text = '''총 데이터: 365,888개 문서 + 2,907개 시계열
처리 시간: 4시간 → 1시간 (75% 단축)
메모리: 13GB → 48.1MB (99.6% 압축)
라벨링: 1,852,138개 문장'''

    stats_box = FancyBboxPatch((12.5, 0.2), 3, 1.2,
                               boxstyle='round,pad=0.05',
                               facecolor=colors['light'], alpha=0.8,
                               edgecolor=colors['border'], linewidth=1)
    ax.add_patch(stats_box)
    ax.text(14, 0.8, stats_text, fontsize=9, ha='center', va='center', color=colors['text'])

    # 범례
    legend_elements = [
        mpatches.Patch(color=colors['primary'], alpha=0.3, label='뉴스 데이터'),
        mpatches.Patch(color=colors['border'], alpha=0.3, label='보조 데이터'),
        mpatches.Patch(color=colors['accent2'], alpha=0.3, label='병렬 처리 (채권)'),
        mpatches.Patch(color=colors['accent1'], alpha=0.3, label='저장소')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9,
             frameon=False)

    plt.tight_layout()
    return fig

def main():
    """메인 실행 함수"""
    print("데이터 수집 파이프라인 다이어그램 생성 중...")

    # 다이어그램 생성
    fig = create_pipeline_diagram()

    # 파일 저장
    output_path = Path(__file__).parent / 'data_collection_pipeline.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ 다이어그램 생성 완료: {output_path}")

    # PDF 버전도 생성 (벡터 그래픽)
    output_pdf = Path(__file__).parent / 'data_collection_pipeline.pdf'
    fig.savefig(output_pdf, format='pdf', bbox_inches='tight', facecolor='white')
    print(f"✓ PDF 버전도 생성: {output_pdf}")

    plt.close()

if __name__ == "__main__":
    main()