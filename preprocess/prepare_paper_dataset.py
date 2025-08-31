#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
논문 재현을 위한 데이터셋 준비 및 스키마 변환 스크립트
Paper: "Deciphering Monetary Policy Board Minutes Through Text Mining Approach"

이 스크립트는 수집된 뉴스 데이터를 논문의 방법론에 맞게 전처리하고
필요한 스키마 구조로 변환합니다.
"""

import json
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PaperDatasetPreparer:
    """논문 재현을 위한 데이터셋 준비 클래스"""
    
    def __init__(self, base_path: str):
        """
        Args:
            base_path: 프로젝트 루트 경로
        """
        self.base_path = Path(base_path)
        self.unified_path = self.base_path / "crawler" / "data" / "unified"
        self.processed_path = self.base_path / "crawler" / "data" / "paper_reproduction"
        
        # 처리된 데이터 저장 디렉토리 생성
        self.processed_path.mkdir(parents=True, exist_ok=True)
        
        # 논문 재현에 필요한 스키마 정의
        self.paper_schema = {
            # 기본 필드 (현재 수집된 데이터)
            "title": str,
            "content": str,
            "date": str,
            "url": str,
            "source": str,
            
            # 추가 필요 필드 (논문 방법론)
            "document_id": str,  # 고유 문서 ID
            "document_type": str,  # news/mpb_minutes/bond_report
            
            # 텍스트 전처리 필드
            "tokenized_content": list,  # eKoNLPy 토큰화 결과
            "pos_tags": list,  # 품사 태깅 결과
            "filtered_tokens": list,  # POS 필터링 후 토큰
            
            # N-gram 필드
            "unigrams": list,
            "bigrams": list,
            "trigrams": list,
            "fourgrams": list,
            "fivegrams": list,
            
            # 감성 분석 필드
            "hawkish_score": float,  # 긴축적 점수
            "dovish_score": float,  # 완화적 점수
            "sentiment_label": str,  # hawkish/dovish/neutral
            "sentiment_confidence": float,  # 예측 신뢰도
            
            # 시장 지표 필드 (Market Approach용)
            "call_rate": Optional[float],  # 콜금리
            "call_rate_change": Optional[float],  # 콜금리 변화
            "market_label": Optional[str],  # 시장 기반 레이블
            
            # 메타데이터
            "year": int,
            "month": int,
            "day": int,
            "preprocessing_date": str,
            "preprocessing_version": str
        }
    
    def load_unified_data(self, year: int, month: Optional[int] = None) -> List[Dict]:
        """
        통합된 뉴스 데이터 로드
        
        Args:
            year: 연도
            month: 월 (None이면 전체 연도 데이터 로드)
        
        Returns:
            뉴스 데이터 리스트
        """
        data = []
        
        if month:
            file_path = self.unified_path / f"news_{year}_{month:02d}.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    month_data = json.load(f)
                    data.extend(month_data)
                    logger.info(f"Loaded {len(month_data)} articles from {file_path.name}")
        else:
            # 전체 연도 데이터 로드
            for month in range(1, 13):
                file_path = self.unified_path / f"news_{year}_{month:02d}.json"
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        month_data = json.load(f)
                        data.extend(month_data)
                        logger.info(f"Loaded {len(month_data)} articles from {file_path.name}")
        
        return data
    
    def add_document_metadata(self, articles: List[Dict]) -> List[Dict]:
        """
        문서 메타데이터 추가
        
        Args:
            articles: 원본 뉴스 기사 리스트
        
        Returns:
            메타데이터가 추가된 기사 리스트
        """
        for idx, article in enumerate(articles):
            # 고유 문서 ID 생성
            date_str = article['date'].replace('-', '').replace(' ', '_').replace(':', '')
            source = article['source']
            article['document_id'] = f"{source}_{date_str}_{idx:06d}"
            
            # 문서 타입
            article['document_type'] = 'news'
            
            # 날짜 파싱
            try:
                dt = datetime.strptime(article['date'], "%Y-%m-%d %H:%M:%S")
                article['year'] = dt.year
                article['month'] = dt.month
                article['day'] = dt.day
            except:
                # 날짜 파싱 실패 시 기본값
                article['year'] = None
                article['month'] = None
                article['day'] = None
            
            # 전처리 메타데이터
            article['preprocessing_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            article['preprocessing_version'] = "1.0.0"
            
            # 초기 감성 분석 필드 (추후 채워질 예정)
            article['hawkish_score'] = None
            article['dovish_score'] = None
            article['sentiment_label'] = None
            article['sentiment_confidence'] = None
            
            # N-gram 필드 초기화
            article['unigrams'] = []
            article['bigrams'] = []
            article['trigrams'] = []
            article['fourgrams'] = []
            article['fivegrams'] = []
            
            # 토큰화 필드 초기화
            article['tokenized_content'] = []
            article['pos_tags'] = []
            article['filtered_tokens'] = []
            
            # 시장 지표 필드 초기화
            article['call_rate'] = None
            article['call_rate_change'] = None
            article['market_label'] = None
        
        return articles
    
    def validate_schema(self, article: Dict) -> bool:
        """
        스키마 검증
        
        Args:
            article: 검증할 기사
        
        Returns:
            스키마 충족 여부
        """
        required_fields = [
            'title', 'content', 'date', 'url', 'source',
            'document_id', 'document_type'
        ]
        
        for field in required_fields:
            if field not in article:
                logger.warning(f"Missing required field: {field}")
                return False
        
        return True
    
    def save_processed_data(self, data: List[Dict], output_filename: str):
        """
        처리된 데이터 저장
        
        Args:
            data: 처리된 데이터
            output_filename: 출력 파일명
        """
        output_path = self.processed_path / output_filename
        
        # JSON 형식으로 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(data)} articles to {output_path}")
        
        # CSV 형식으로도 저장 (분석 용이성)
        csv_path = output_path.with_suffix('.csv')
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        logger.info(f"Also saved as CSV: {csv_path}")
    
    def create_summary_stats(self, data: List[Dict]) -> Dict:
        """
        데이터 요약 통계 생성
        
        Args:
            data: 처리된 데이터
        
        Returns:
            요약 통계
        """
        df = pd.DataFrame(data)
        
        stats = {
            "total_documents": len(data),
            "sources": df['source'].value_counts().to_dict(),
            "documents_by_month": df.groupby(['year', 'month']).size().to_dict(),
            "average_content_length": df['content'].str.len().mean(),
            "date_range": {
                "start": df['date'].min(),
                "end": df['date'].max()
            },
            "schema_fields": list(df.columns),
            "null_counts": df.isnull().sum().to_dict()
        }
        
        return stats
    
    def prepare_paper_dataset(self, year: int):
        """
        논문 재현을 위한 전체 데이터셋 준비
        
        Args:
            year: 처리할 연도
        """
        logger.info(f"Starting dataset preparation for year {year}")
        
        # 1. 데이터 로드
        logger.info("Loading unified data...")
        articles = self.load_unified_data(year)
        logger.info(f"Loaded total {len(articles)} articles")
        
        # 2. 메타데이터 추가
        logger.info("Adding document metadata...")
        articles = self.add_document_metadata(articles)
        
        # 3. 스키마 검증
        logger.info("Validating schema...")
        valid_articles = [a for a in articles if self.validate_schema(a)]
        logger.info(f"Valid articles: {len(valid_articles)}/{len(articles)}")
        
        # 4. 데이터 저장
        output_filename = f"paper_dataset_{year}.json"
        self.save_processed_data(valid_articles, output_filename)
        
        # 5. 요약 통계 생성
        stats = self.create_summary_stats(valid_articles)
        stats_filename = f"paper_dataset_{year}_stats.json"
        stats_path = self.processed_path / stats_filename
        
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Dataset preparation completed for year {year}")
        logger.info(f"Summary statistics saved to {stats_filename}")
        
        return valid_articles, stats


def main():
    """메인 실행 함수"""
    # 프로젝트 루트 경로 설정
    base_path = "/Users/lord_jubin/Desktop/my_git/mpb-stance-mining"
    
    # 데이터셋 준비 객체 생성
    preparer = PaperDatasetPreparer(base_path)
    
    # 2015년 데이터 처리
    articles, stats = preparer.prepare_paper_dataset(2015)
    
    # 결과 출력
    print("\n=== Dataset Preparation Results ===")
    print(f"Total documents processed: {stats['total_documents']}")
    print(f"\nDocuments by source:")
    for source, count in stats['sources'].items():
        print(f"  - {source}: {count:,}")
    print(f"\nDate range: {stats['date_range']['start']} to {stats['date_range']['end']}")
    print(f"\nOutput location: {preparer.processed_path}")
    
    # 다음 단계 안내
    print("\n=== Next Steps ===")
    print("1. Run eKoNLPy preprocessing: python preprocess/apply_ekonlpy.py")
    print("2. Extract n-grams: python preprocess/extract_ngrams.py")
    print("3. Apply sentiment analysis: python modeling/sentiment_analysis.py")
    print("4. Merge with market data: python preprocess/merge_market_data.py")


if __name__ == "__main__":
    main()