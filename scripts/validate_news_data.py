#!/usr/bin/env python3
"""
뉴스 데이터 품질 검증 스크립트
2014-2025년 수집된 뉴스 데이터의 완전성과 품질을 검증
"""

import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import statistics

def validate_news_data(base_path="/Users/lord_jubin/Desktop/my_git/mpb-stance-mining"):
    """뉴스 데이터 검증 메인 함수"""
    
    data_path = Path(base_path) / "crawler" / "data" / "unified"
    
    # 통계 변수
    total_articles = 0
    articles_by_source = defaultdict(int)
    articles_by_year = defaultdict(int)
    articles_by_month = defaultdict(int)
    content_lengths = []
    missing_content = 0
    truncated_content = 0
    duplicate_urls = set()
    seen_urls = set()
    
    # 모든 뉴스 파일 처리
    news_files = sorted(data_path.glob("news_*.json"))
    print(f"총 {len(news_files)}개 파일 발견\n")
    
    for file_path in news_files:
        # 파일명에서 연도와 월 추출
        filename = file_path.stem  # news_2014_01
        parts = filename.split('_')
        year = int(parts[1])
        month = int(parts[2])
        
        print(f"처리 중: {filename}...", end=" ")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            month_total = 0
            
            # 각 소스별 기사 처리
            for source, articles in data.items():
                if not isinstance(articles, list):
                    continue
                    
                for article in articles:
                    total_articles += 1
                    month_total += 1
                    articles_by_source[source] += 1
                    articles_by_year[year] += 1
                    articles_by_month[f"{year}-{month:02d}"] += 1
                    
                    # 콘텐츠 검증
                    content = article.get('content', '')
                    if not content:
                        missing_content += 1
                    else:
                        content_len = len(content)
                        content_lengths.append(content_len)
                        
                        # 3000자에서 잘렸는지 확인
                        if content_len == 3000:
                            truncated_content += 1
                    
                    # URL 중복 확인
                    url = article.get('url', '')
                    if url:
                        if url in seen_urls:
                            duplicate_urls.add(url)
                        seen_urls.add(url)
            
            print(f"{month_total}개 기사")
            
        except Exception as e:
            print(f"오류: {e}")
    
    # 통계 계산
    avg_length = statistics.mean(content_lengths) if content_lengths else 0
    median_length = statistics.median(content_lengths) if content_lengths else 0
    min_length = min(content_lengths) if content_lengths else 0
    max_length = max(content_lengths) if content_lengths else 0
    
    # 결과 출력
    print("\n" + "="*60)
    print("뉴스 데이터 검증 결과")
    print("="*60)
    
    print(f"\n📊 전체 통계:")
    print(f"  - 총 기사 수: {total_articles:,}개")
    print(f"  - 파일 수: {len(news_files)}개")
    print(f"  - 기간: 2014-01 ~ 2025-12")
    
    print(f"\n📈 소스별 분포:")
    for source, count in sorted(articles_by_source.items()):
        percentage = (count / total_articles * 100) if total_articles > 0 else 0
        print(f"  - {source}: {count:,}개 ({percentage:.1f}%)")
    
    print(f"\n📅 연도별 분포:")
    for year in sorted(articles_by_year.keys()):
        count = articles_by_year[year]
        print(f"  - {year}년: {count:,}개")
    
    print(f"\n📝 콘텐츠 품질:")
    print(f"  - 평균 길이: {avg_length:,.0f}자")
    print(f"  - 중간값 길이: {median_length:,.0f}자")
    print(f"  - 최소 길이: {min_length:,}자")
    print(f"  - 최대 길이: {max_length:,}자")
    print(f"  - 빈 콘텐츠: {missing_content}개 ({missing_content/total_articles*100:.2f}%)")
    print(f"  - 3000자 절단 의심: {truncated_content}개 ({truncated_content/total_articles*100:.2f}%)")
    
    print(f"\n🔍 데이터 무결성:")
    print(f"  - 중복 URL: {len(duplicate_urls)}개")
    print(f"  - 고유 URL: {len(seen_urls)}개")
    
    # 품질 점수 계산
    quality_score = 100
    if missing_content > 0:
        quality_score -= (missing_content / total_articles * 20)
    if truncated_content > 0:
        quality_score -= (truncated_content / total_articles * 10)
    if len(duplicate_urls) > 0:
        quality_score -= (len(duplicate_urls) / total_articles * 10)
    if avg_length < 1000:
        quality_score -= 10
    
    print(f"\n✅ 품질 점수: {quality_score:.1f}/100")
    
    if quality_score >= 90:
        print("   → 우수: 데이터 품질이 매우 좋습니다!")
    elif quality_score >= 80:
        print("   → 양호: 대부분의 데이터가 사용 가능합니다.")
    elif quality_score >= 70:
        print("   → 보통: 일부 개선이 필요합니다.")
    else:
        print("   → 주의: 데이터 품질 개선이 필요합니다.")
    
    # 결과를 JSON으로 저장
    validation_result = {
        "validation_date": datetime.now().isoformat(),
        "total_articles": total_articles,
        "files_processed": len(news_files),
        "articles_by_source": dict(articles_by_source),
        "articles_by_year": dict(articles_by_year),
        "content_stats": {
            "avg_length": avg_length,
            "median_length": median_length,
            "min_length": min_length,
            "max_length": max_length,
            "missing_content": missing_content,
            "truncated_suspects": truncated_content
        },
        "integrity": {
            "duplicate_urls": len(duplicate_urls),
            "unique_urls": len(seen_urls)
        },
        "quality_score": quality_score
    }
    
    output_path = Path(base_path) / "data" / "news_validation_report.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(validation_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 검증 보고서 저장: {output_path}")
    
    return validation_result

if __name__ == "__main__":
    validate_news_data()