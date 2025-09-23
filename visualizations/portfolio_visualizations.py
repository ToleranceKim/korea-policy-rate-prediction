#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
portfolio_visualizations.py
포트폴리오 프레젠테이션을 위한 추가 시각화 생성
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Patch
from matplotlib.patches import Rectangle
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent

# 색상 테마 (타겟팅된 시인성 개선)
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
import matplotlib
matplotlib.use('Agg')
import platform
import matplotlib.font_manager as fm
from matplotlib import rcParams

if platform.system() == 'Darwin':
    font_path = '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname=font_path)
    font_name = font_prop.get_name()

    rcParams['font.family'] = font_name
    rcParams['axes.unicode_minus'] = False
    plt.rcParams['font.family'] = font_name
    plt.rcParams['axes.unicode_minus'] = False
    matplotlib.rc('font', family=font_name)

sns.set_style("whitegrid")
plt.rcParams['font.family'] = 'Arial Unicode MS'
matplotlib.rc('font', family='Arial Unicode MS')


def create_call_rate_labeling():
    """일별 콜금리 추이와 1개월 후 변동 기반 라벨링 시각화"""
    print("\n1. Creating call rate labeling visualization...")

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

    # 월별 집계
    df_call['year_month'] = df_call['date'].dt.to_period('M')
    monthly_agg = df_call.groupby(['year_month', 'label']).size().unstack(fill_value=0)

    print(f"   Data period: {df_call['date'].min().strftime('%Y-%m-%d')} to {df_call['date'].max().strftime('%Y-%m-%d')}")
    print(f"   Total days: {len(df_call)}")
    print(f"   Days labeled Hawkish: {len(df_call[df_call['label'] == 'Hawkish'])}")
    print(f"   Days labeled Dovish: {len(df_call[df_call['label'] == 'Dovish'])}")
    print(f"   Days with no label (±3bp): {len(df_call[df_call['label'] == 'None'])}")

    # 첫 번째 차트: 일별 콜금리 추이와 라벨
    fig1, ax1 = plt.subplots(figsize=(16, 8), facecolor='white')

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
                    ax1.axvspan(period_start, period_end, alpha=alpha, color='gray', zorder=1)
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
                ax1.axvline(x=row['date'], color='darkgray', linestyle='--', alpha=0.3, linewidth=0.8, zorder=2)
                if row['change'] > 0:
                    ax1.annotate('↑', xy=(row['date'], 4.2), fontsize=10, color='red', ha='center')
                elif row['change'] < 0:
                    ax1.annotate('↓', xy=(row['date'], 4.2), fontsize=10, color='green', ha='center')
    except Exception as e:
        print(f"   Note: Could not load rate decision dates: {e}")

    # 콜금리 라인 차트
    ax1.plot(df_call['date'], df_call['call_rate'],
            color=THEME_COLORS['primary_blue'], linewidth=1.5, alpha=0.8, label='일별 콜금리', zorder=2)

    # 모든 Hawkish/Dovish 포인트 표시 (샘플링 없이)
    hawkish_points = df_call[df_call['label'] == 'Hawkish']
    dovish_points = df_call[df_call['label'] == 'Dovish']

    # Hawkish 포인트 (1개월 후 상승) - 모두 표시
    ax1.scatter(hawkish_points['date'], hawkish_points['call_rate'],
               color=THEME_COLORS['hawkish_red'], s=15, zorder=3,
               marker='^', alpha=0.4, edgecolors='none', label=f'Hawkish ({len(hawkish_points)}일)')

    # Dovish 포인트 (1개월 후 하락) - 모두 표시
    ax1.scatter(dovish_points['date'], dovish_points['call_rate'],
               color=THEME_COLORS['dovish_green'], s=15, zorder=3,
               marker='v', alpha=0.4, edgecolors='none', label=f'Dovish ({len(dovish_points)}일)')

    # 텍스트 박스 - 실제 라벨링 방법 설명
    textstr = f'''실제 라벨링 방법 (논문 재현):
· 각 날짜의 콜금리 → 1개월 후 콜금리 비교
· 변동 > +3bp → Hawkish ({len(df_call[df_call['label'] == 'Hawkish'])}일)
· 변동 < -3bp → Dovish ({len(df_call[df_call['label'] == 'Dovish'])}일)
· ±3bp 이내 → 라벨 없음 ({len(df_call[df_call['label'] == 'None'])}일)'''

    props = dict(boxstyle='round,pad=0.6',
                facecolor=THEME_COLORS['lighter_blue'],
                edgecolor=THEME_COLORS['primary_blue'],
                alpha=0.95)
    ax1.text(0.02, 0.97, textstr, transform=ax1.transAxes, fontsize=10,
            verticalalignment='top', bbox=props, fontweight='bold')

    ax1.set_title('시장 반응 기반(Market-based) 라벨링: 일별 콜금리와 1개월 후 변동',
                 fontsize=16, fontweight='bold', color=THEME_COLORS['text_color'])
    ax1.set_ylabel('콜금리 (%)', fontsize=12, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.3, color=THEME_COLORS['grid_color'])
    ax1.set_ylim(0, 4.5)

    # 범례 설명 업데이트
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
    ax1.legend(handles=legend_elements, loc='upper right', frameon=True,
              fancybox=True, shadow=True, fontsize=9)

    plt.tight_layout()
    plt.savefig('call_rate_daily_labeling.png', dpi=300, bbox_inches='tight',
                facecolor='white', transparent=True)
    plt.close()
    print("   ✓ Saved call_rate_daily_labeling.png")

    # 두 번째 차트: 월별 라벨 분포
    fig2, ax2 = plt.subplots(figsize=(16, 6), facecolor='white')

    # 월별 집계 막대그래프
    if 'Hawkish' in monthly_agg.columns and 'Dovish' in monthly_agg.columns:
        monthly_agg[['Hawkish', 'Dovish']].plot(kind='bar', stacked=True, ax=ax2,
                                                 color=[THEME_COLORS['hawkish_red'],
                                                        THEME_COLORS['dovish_green']],
                                                 alpha=0.8, width=0.9)

    ax2.set_title('월별 라벨링 분포 (일 단위 집계)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('기간', fontsize=12, fontweight='bold')
    ax2.set_ylabel('라벨링된 일수', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper left', fontsize=10)
    ax2.grid(True, linestyle='--', alpha=0.3, axis='y')

    # x축 라벨 간소화 (너무 많아서)
    ax2.set_xticklabels([str(label)[:7] if i % 6 == 0 else ''
                         for i, label in enumerate(ax2.get_xticklabels())],
                        rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig('call_rate_monthly_distribution.png', dpi=300, bbox_inches='tight',
                facecolor='white', transparent=True)
    plt.close()
    print("   ✓ Saved call_rate_monthly_distribution.png")


def create_ngram_funnel():
    """N-gram 필터링 깔때기 시각화"""
    print("\n2. Creating N-gram funnel visualization...")

    fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')

    # 깔때기 데이터
    stages = ['초기 N-grams\n생성', '빈도 필터\n(freq > 5)', '최종 특징']
    values = [53371110, 10000000, 1577569]  # 중간 값은 시각적 효과를 위한 추정
    colors = [THEME_COLORS['lighter_blue'],
             THEME_COLORS['light_blue'],
             THEME_COLORS['primary_blue']]

    # 깔때기 그리기
    y_positions = [0.8, 0.5, 0.2]
    widths = [0.8, 0.5, 0.3]

    for i, (stage, value, color, y_pos, width) in enumerate(zip(stages, values, colors, y_positions, widths)):
        # 사각형 (깔때기 단계)
        rect = FancyBboxPatch((0.5 - width/2, y_pos - 0.1), width, 0.15,
                              boxstyle="round,pad=0.01",
                              facecolor=color, edgecolor='white', linewidth=2)
        ax.add_patch(rect)

        # 텍스트 (가독성 개선 - 외곽선 추가)
        text_color = 'white' if i == 2 else THEME_COLORS['text_color']
        # 텍스트에 외곽선 추가로 가독성 개선
        for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
            ax.text(0.5 + dx*0.001, y_pos + dy*0.001, stage, ha='center', va='center',
                   fontsize=12, fontweight='bold', color='white', alpha=0.8)
        ax.text(0.5, y_pos, stage, ha='center', va='center',
               fontsize=12, fontweight='bold', color=text_color)

        # 숫자 표시
        if i == 0:
            num_text = '53,371,110'
            ax.text(0.5 + width/2 + 0.05, y_pos, num_text,
                   ha='left', va='center', fontsize=14, fontweight='bold',
                   color=THEME_COLORS['text_color'])
        elif i == 2:
            num_text = '1,577,569'
            ax.text(0.5 + width/2 + 0.05, y_pos, num_text,
                   ha='left', va='center', fontsize=14, fontweight='bold',
                   color=THEME_COLORS['text_color'])

        # 화살표
        if i < len(stages) - 1:
            arrow = FancyArrowPatch((0.5, y_pos - 0.12), (0.5, y_positions[i+1] + 0.12),
                                  arrowstyle='->', mutation_scale=20,
                                  color=THEME_COLORS['text_color'], linewidth=2)
            ax.add_patch(arrow)

    # 97% 노이즈 제거 강조
    ax.text(0.9, 0.5, '97%\n노이즈 제거',
           ha='center', va='center', fontsize=16, fontweight='bold',
           color=THEME_COLORS['orange_dash'],
           bbox=dict(boxstyle='round,pad=0.5',
                    facecolor='white',
                    edgecolor=THEME_COLORS['orange_dash'],
                    linewidth=2))

    # 타이틀
    ax.text(0.5, 0.95, 'N-gram 특징 필터링 프로세스',
           ha='center', va='center', fontsize=18, fontweight='bold',
           color=THEME_COLORS['text_color'])

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    plt.tight_layout()
    plt.savefig('ngram_funnel.png', dpi=300, bbox_inches='tight',
                facecolor='white', transparent=True)
    plt.close()
    print("   ✓ Saved ngram_funnel.png")


def create_ngram_combination():
    """N-gram 결합 다이어그램"""
    print("\n3. Creating N-gram combination diagram...")

    fig, ax = plt.subplots(figsize=(12, 5), facecolor='white')

    # 박스 위치
    box1_x, box1_y = 0.15, 0.5
    box2_x, box2_y = 0.35, 0.5
    box3_x, box3_y = 0.65, 0.5

    # 단어 박스
    box_style = "round,pad=0.3"

    # "금리" 박스
    box1 = FancyBboxPatch((box1_x - 0.06, box1_y - 0.08), 0.12, 0.16,
                          boxstyle=box_style,
                          facecolor=THEME_COLORS['light_blue'],
                          edgecolor=THEME_COLORS['primary_blue'],
                          linewidth=2)
    ax.add_patch(box1)
    ax.text(box1_x, box1_y, '금리', ha='center', va='center',
           fontsize=16, fontweight='bold', color=THEME_COLORS['text_color'])

    # "인상" 박스
    box2 = FancyBboxPatch((box2_x - 0.06, box2_y - 0.08), 0.12, 0.16,
                          boxstyle=box_style,
                          facecolor=THEME_COLORS['light_blue'],
                          edgecolor=THEME_COLORS['primary_blue'],
                          linewidth=2)
    ax.add_patch(box2)
    ax.text(box2_x, box2_y, '인상', ha='center', va='center',
           fontsize=16, fontweight='bold', color=THEME_COLORS['text_color'])

    # + 기호
    ax.text((box1_x + box2_x) / 2, box1_y, '+', ha='center', va='center',
           fontsize=20, fontweight='bold', color=THEME_COLORS['text_color'])

    # 화살표
    arrow = FancyArrowPatch((box2_x + 0.08, box2_y), (box3_x - 0.12, box3_y),
                          arrowstyle='->', mutation_scale=30,
                          color=THEME_COLORS['primary_blue'], linewidth=3)
    ax.add_patch(arrow)

    # "금리 인상" 박스 (결과)
    box3 = FancyBboxPatch((box3_x - 0.12, box3_y - 0.08), 0.24, 0.16,
                          boxstyle=box_style,
                          facecolor=THEME_COLORS['dovish_green'],
                          edgecolor=THEME_COLORS['green_star'],
                          linewidth=3)
    ax.add_patch(box3)
    ax.text(box3_x, box3_y, '금리 인상', ha='center', va='center',
           fontsize=18, fontweight='bold', color=THEME_COLORS['text_color'])

    # 설명 텍스트
    ax.text(0.5, 0.15, 'Unigram (단일 단어) → Bigram (2-word 조합)',
           ha='center', va='center', fontsize=12,
           color=THEME_COLORS['text_color'], style='italic')

    ax.text(0.5, 0.85, 'N-gram: 문맥 정보를 포착하는 단어 조합',
           ha='center', va='center', fontsize=18, fontweight='bold',
           color=THEME_COLORS['text_color'])

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    plt.tight_layout()
    plt.savefig('ngram_combination.png', dpi=300, bbox_inches='tight',
                facecolor='white', transparent=True)
    plt.close()
    print("   ✓ Saved ngram_combination.png")


def create_performance_improvement():
    """성능 개선 곡선 시각화"""
    print("\n4. Creating performance improvement curve...")

    fig, ax = plt.subplots(figsize=(12, 7), facecolor='white')

    # 데이터
    versions = ['v1\n(날짜 단위)', 'v2\n(필터링)', 'v3\n(POS 태깅)',
                'v4\n(빈도>5)', 'v5\n(문장 단위)']
    f1_scores = [1.0, 0.62, 0.64, 0.65, 0.793]  # v1은 과적합 100%
    sample_sizes = [1405, 1405, 1405, 1405, 1851040]  # 샘플 수

    # F1-Score 곡선
    x = np.arange(len(versions))
    ax.plot(x, f1_scores, 'o-', linewidth=3, markersize=10,
           color=THEME_COLORS['primary_blue'], label='F1-Score')

    # 각 점에 대한 마커 및 텍스트
    for i, (v, score, samples) in enumerate(zip(versions, f1_scores, sample_sizes)):
        if i == 0:  # v1 과적합
            ax.scatter(i, score, s=200, color='red', zorder=5)
            ax.annotate(f'과적합\nF1={score:.1%}',
                       xy=(i, score), xytext=(i, score - 0.15),
                       ha='center', fontsize=10, color='red',
                       arrowprops=dict(arrowstyle='->', color='red', lw=1))
        elif i == len(versions) - 1:  # v5 최종
            ax.scatter(i, score, s=200, color=THEME_COLORS['green_star'], zorder=5)
            ax.annotate(f'최종 성능\nF1={score:.1%}',
                       xy=(i, score), xytext=(i + 0.2, score + 0.05),
                       ha='left', fontsize=11, fontweight='bold',
                       color=THEME_COLORS['green_star'],
                       arrowprops=dict(arrowstyle='->',
                                     color=THEME_COLORS['green_star'], lw=2))
        else:
            ax.scatter(i, score, s=100, color=THEME_COLORS['primary_blue'], zorder=5)
            ax.text(i, score + 0.03, f'{score:.1%}', ha='center', fontsize=9)

    # 샘플 수 증가 표시
    ax.annotate('', xy=(4, 0.5), xytext=(4, 0.3),
               arrowprops=dict(arrowstyle='<->', color=THEME_COLORS['orange_dash'],
                             lw=2))
    ax.text(4.2, 0.4, f'샘플 수\n1,317배 증가\n({sample_sizes[0]:,}→{sample_sizes[-1]:,})',
           fontsize=11, fontweight='bold', color=THEME_COLORS['orange_dash'],
           bbox=dict(boxstyle='round,pad=0.3',
                    facecolor=THEME_COLORS['lighter_blue'],
                    edgecolor=THEME_COLORS['orange_dash']))

    # 축 설정
    ax.set_xticks(x)
    ax.set_xticklabels(versions)
    ax.set_ylabel('F1-Score', fontsize=12, fontweight='bold')
    ax.set_xlabel('모델 버전', fontsize=12, fontweight='bold')
    ax.set_ylim(0.2, 1.1)

    # 타이틀
    ax.set_title('과적합 해결 및 일반화 성능 확보 과정',
                fontsize=16, fontweight='bold', color=THEME_COLORS['text_color'])

    # 그리드 및 스타일
    ax.grid(True, linestyle='--', alpha=0.3, color=THEME_COLORS['grid_color'])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # 범례
    ax.legend(loc='lower right', frameon=True, fancybox=True, shadow=True)

    plt.tight_layout()
    plt.savefig('performance_improvement.png', dpi=300, bbox_inches='tight',
                facecolor='white', transparent=True)
    plt.close()
    print("   ✓ Saved performance_improvement.png")


def main():
    """메인 실행 함수"""
    print("="*60)
    print("Portfolio Visualizations Generation")
    print("="*60)

    # 비주얼리제이션 디렉토리로 이동
    import os
    viz_dir = PROJECT_ROOT / 'visualizations'
    os.chdir(viz_dir)

    # 각 시각화 생성
    create_call_rate_labeling()
    create_ngram_funnel()
    create_ngram_combination()
    create_performance_improvement()

    print("\n" + "="*60)
    print("✅ All portfolio visualizations created successfully!")
    print(f"Location: {viz_dir}")

    # 생성된 파일 목록
    print("\nGenerated files:")
    for file in ['call_rate_labeling.png', 'ngram_funnel.png',
                 'ngram_combination.png', 'performance_improvement.png']:
        if Path(file).exists():
            size_kb = os.path.getsize(file) / 1024
            print(f"  - {file} ({size_kb:.1f} KB)")
    print("="*60)


if __name__ == "__main__":
    main()