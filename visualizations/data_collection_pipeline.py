#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
data_collection_pipeline.py
전체 데이터 수집 파이프라인 다이어그램 생성
"""

import graphviz
from pathlib import Path

def create_pipeline_diagram():
    """전문적인 데이터 수집 파이프라인 다이어그램 생성"""

    # Graphviz 다이어그램 초기화
    dot = graphviz.Digraph(comment='Data Collection Pipeline', format='png')
    dot.attr(rankdir='TB', bgcolor='white', dpi='300')  # 고해상도
    dot.attr(fontname='Arial', fontsize='11')

    # 전체 그래프 스타일
    dot.attr('graph', splines='ortho', nodesep='0.5', ranksep='0.8')

    # 노드 기본 스타일
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial',
             fontsize='10', height='0.6', width='1.8')

    # 엣지 기본 스타일
    dot.attr('edge', fontsize='9', fontname='Arial')

    # ===== 1단계: 데이터 소스 (최상단) =====
    with dot.subgraph(name='cluster_sources') as c:
        c.attr(label='데이터 소스 (365,890개 문서 + 2,891개 시계열)',
               style='rounded,filled', fillcolor='#f0f0f0', fontsize='12', fontweight='bold')
        c.attr('node', shape='box3d', style='filled', fontweight='bold')

        # 뉴스 소스
        c.node('YNA', '연합뉴스\n69,544개\n(19.4%)', fillcolor='#e3f2fd', fontsize='10')
        c.node('ED', '이데일리\n112,201개\n(31.2%)', fillcolor='#fff3e0', fontsize='10')
        c.node('IM', '인포맥스\n177,406개\n(49.4%)', fillcolor='#f3e5f5', fontsize='10')

        # 기타 소스
        c.node('MPB', 'MPB 의사록\n224개 PDF\n(월 2회)', fillcolor='#e8f5e9', fontsize='10')
        c.node('RATE', '금리 데이터\n콜금리: 2,866개\n기준금리: 41개', fillcolor='#fce4ec', fontsize='10')
        c.node('BOND', '채권 리포트\n6,515개\n(네이버금융)', fillcolor='#fff8e1', fontsize='10')

    # ===== 2단계: 수집 방법 =====
    with dot.subgraph(name='cluster_methods') as c:
        c.attr(label='수집 방법', style='rounded,filled', fillcolor='#f5f5f5', fontsize='12')
        c.attr('node', shape='ellipse', style='filled')

        c.node('API', 'REST API\nJSON Response\n(2016-2025)', fillcolor='#e1f5fe', fontsize='9')
        c.node('CRAWL1', 'HTML 크롤링\nScrapy/BS4', fillcolor='#fff3e0', fontsize='9')
        c.node('CRAWL2', 'Ajax 크롤링\n전체 본문 추출', fillcolor='#f3e5f5', fontsize='9')
        c.node('PDF', 'PDF 크롤링\nPyPDF2 추출', fillcolor='#e8f5e9', fontsize='9')
        c.node('CSV', 'CSV 다운로드\nKOSIS/한은', fillcolor='#fce4ec', fontsize='9')

    # ===== 3단계: 병렬 처리 =====
    dot.node('POOL', 'ThreadPoolExecutor\nmax_workers=5\n4,500개/시간 (4.5x↑)',
             shape='box3d', style='filled,bold', fillcolor='#ffebee', fontsize='11')

    # ===== 4단계: 전처리 파이프라인 =====
    with dot.subgraph(name='cluster_process') as c:
        c.attr(label='전처리 파이프라인', style='rounded,filled', fillcolor='#f0f5f0', fontsize='12')
        c.attr('node', shape='box', style='filled')

        c.node('RETRY', '재시도 로직\n3회 시도\nExponential Backoff\n(2s → 4s → 8s)',
               fillcolor='#fff9c4', fontsize='9')
        c.node('DEDUP', '중복 제거\nURL + 제목/날짜\n228개 제거 (0.06%)',
               fillcolor='#f0f4c3', fontsize='9')
        c.node('CLEAN', '통합 정제\nunified_cleansing.py\n34.6% 노이즈 제거',
               fillcolor='#dcedc8', fontsize='9')
        c.node('VALID', '품질 검증\n수집률: 99.8%\n실패: 0.2%',
               fillcolor='#c8e6c9', fontsize='9')

    # ===== 5단계: 토큰화 =====
    dot.node('TOKEN', 'eKoNLPy + Mecab\n형태소 분석\nPOS 필터링 (60% 제거)\n원본 5.5GB → N-gram 7.5GB',
             shape='parallelogram', style='filled', fillcolor='#e1bee7', fontsize='10')

    # ===== 6단계: 저장 =====
    dot.node('DB', 'PostgreSQL\nJSONB Storage\n85개 필드 스키마\nBatch Insert (1000)',
             shape='cylinder', style='filled,bold', fillcolor='#c5e1a5', fontsize='11')

    # ===== 엣지 연결 =====
    # 뉴스 소스 연결
    dot.edge('YNA', 'API', label='2016-2025')
    dot.edge('YNA', 'CRAWL1', label='2014-2015', style='dashed')
    dot.edge('ED', 'CRAWL2', label='Ajax')
    dot.edge('IM', 'CRAWL1', label='Session')

    # 기타 소스 연결
    dot.edge('MPB', 'PDF', label='토의/결정')
    dot.edge('RATE', 'CSV', label='일별')
    dot.edge('BOND', 'CRAWL1', label='증권사')

    # 수집 방법 → 병렬 처리
    for method in ['API', 'CRAWL1', 'CRAWL2', 'PDF', 'CSV']:
        dot.edge(method, 'POOL')

    # 병렬 처리 → 전처리
    dot.edge('POOL', 'RETRY')
    dot.edge('RETRY', 'DEDUP')
    dot.edge('DEDUP', 'CLEAN')
    dot.edge('CLEAN', 'VALID')

    # 전처리 → 토큰화 → 저장
    dot.edge('VALID', 'TOKEN')
    dot.edge('TOKEN', 'DB')

    # ===== 통계 정보 추가 =====
    with dot.subgraph(name='cluster_stats') as c:
        c.attr(label='최종 결과', style='rounded,filled', fillcolor='#e8eaf6', fontsize='12')
        c.node('STATS', '''총 데이터: 365,890개 문서 + 2,891개 시계열
처리 시간: 4시간 → 1시간 (75% 단축)
전체 프로젝트: 24GB (crawler 5.6GB, preprocess 10GB, modeling 5.4GB)
최종 vocabulary: 15MB (1.9M n-grams)
라벨링: 2,823,248개 문장''',
               shape='note', style='filled', fillcolor='white', fontsize='10')

    dot.edge('DB', 'STATS', style='dashed', label='완료')

    return dot

def main():
    """메인 실행 함수"""
    print("데이터 수집 파이프라인 다이어그램 생성 중...")

    # 다이어그램 생성
    dot = create_pipeline_diagram()

    # 파일 저장
    output_path = Path(__file__).parent / 'data_collection_pipeline'
    dot.render(output_path, format='png', cleanup=True)

    print(f"✓ 다이어그램 생성 완료: {output_path}.png")

    # SVG 버전도 생성 (확대 가능)
    dot.format = 'svg'
    dot.render(output_path, cleanup=True)
    print(f"✓ SVG 버전도 생성: {output_path}.svg")

if __name__ == "__main__":
    main()