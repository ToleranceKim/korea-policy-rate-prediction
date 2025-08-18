#!/usr/bin/env python3
"""
월별 수집 데이터 병합 시스템
- 월별로 수집된 JSON 파일들을 통합
- 중복 제거 및 데이터 검증
- 최종 통합 파일 생성
"""

import json
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime
import hashlib

class DataMerger:
    def __init__(self, base_dir="/Users/lord_jubin/Desktop/my_git/mpb-stance-mining/crawler"):
        self.base_dir = Path(base_dir)
        self.monthly_dir = self.base_dir / "data" / "monthly"
        self.merged_dir = self.base_dir / "data" / "merged"
        self.merged_dir.mkdir(exist_ok=True)
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.base_dir / "logs" / "data_merger.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def generate_content_hash(self, item):
        """컨텐츠 해시 생성 (중복 제거용)"""
        # 제목과 컨텐츠를 기반으로 해시 생성
        content_key = f"{item.get('title', '')}{item.get('content', '')}"
        return hashlib.md5(content_key.encode('utf-8')).hexdigest()
    
    def load_monthly_data(self, crawler_name):
        """특정 크롤러의 월별 데이터 로드"""
        monthly_files = list(self.monthly_dir.glob(f"{crawler_name}_*.json"))
        monthly_files.sort()  # 날짜순 정렬
        
        all_data = []
        duplicate_hashes = set()
        
        self.logger.info(f"📂 Loading {len(monthly_files)} monthly files for {crawler_name}")
        
        for file_path in monthly_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if isinstance(data, list):
                    # 중복 제거
                    for item in data:
                        content_hash = self.generate_content_hash(item)
                        if content_hash not in duplicate_hashes:
                            item['content_hash'] = content_hash
                            item['source_file'] = file_path.name
                            all_data.append(item)
                            duplicate_hashes.add(content_hash)
                        else:
                            self.logger.debug(f"Duplicate found in {file_path.name}: {item.get('title', 'No title')[:50]}...")
                else:
                    # 단일 아이템
                    content_hash = self.generate_content_hash(data)
                    if content_hash not in duplicate_hashes:
                        data['content_hash'] = content_hash
                        data['source_file'] = file_path.name
                        all_data.append(data)
                        duplicate_hashes.add(content_hash)
                        
            except Exception as e:
                self.logger.error(f"Error loading {file_path}: {e}")
        
        self.logger.info(f"✅ Loaded {len(all_data)} unique items for {crawler_name}")
        return all_data
    
    def validate_data_quality(self, data, crawler_name):
        """데이터 품질 검증"""
        issues = []
        
        for i, item in enumerate(data):
            # 필수 필드 확인
            required_fields = ['title', 'content', 'date']
            missing_fields = [field for field in required_fields if not item.get(field)]
            
            if missing_fields:
                issues.append(f"Item {i}: Missing fields {missing_fields}")
            
            # 내용 길이 확인
            content_length = len(item.get('content', ''))
            if content_length < 50:
                issues.append(f"Item {i}: Content too short ({content_length} chars)")
            
            # 날짜 형식 확인
            date_str = item.get('date', '')
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                issues.append(f"Item {i}: Invalid date format '{date_str}'")
        
        if issues:
            self.logger.warning(f"⚠️ {crawler_name} data quality issues: {len(issues)} problems found")
            for issue in issues[:10]:  # 처음 10개만 출력
                self.logger.warning(f"  {issue}")
            if len(issues) > 10:
                self.logger.warning(f"  ... and {len(issues) - 10} more issues")
        else:
            self.logger.info(f"✅ {crawler_name} data quality: No issues found")
        
        return issues
    
    def create_summary_statistics(self, data, crawler_name):
        """데이터 요약 통계 생성"""
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        
        # 날짜별 분포
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        date_stats = {
            'earliest_date': df['date'].min().strftime('%Y-%m-%d') if df['date'].min() else None,
            'latest_date': df['date'].max().strftime('%Y-%m-%d') if df['date'].max() else None,
            'total_items': len(df),
            'date_range_months': ((df['date'].max() - df['date'].min()).days / 30.44) if df['date'].min() and df['date'].max() else 0
        }
        
        # 컨텐츠 통계
        content_stats = {
            'avg_content_length': df['content'].str.len().mean() if 'content' in df else 0,
            'min_content_length': df['content'].str.len().min() if 'content' in df else 0,
            'max_content_length': df['content'].str.len().max() if 'content' in df else 0
        }
        
        # 관련성 점수 통계 (있는 경우)
        relevance_stats = {}
        if 'relevance_score' in df.columns:
            relevance_stats = {
                'avg_relevance_score': df['relevance_score'].mean(),
                'min_relevance_score': df['relevance_score'].min(),
                'max_relevance_score': df['relevance_score'].max()
            }
        
        return {
            'crawler_name': crawler_name,
            'date_statistics': date_stats,
            'content_statistics': content_stats,
            'relevance_statistics': relevance_stats,
            'generated_at': datetime.now().isoformat()
        }
    
    def merge_crawler_data(self, crawler_name):
        """특정 크롤러의 데이터 병합"""
        self.logger.info(f"🔄 Starting merge for {crawler_name}")
        
        # 월별 데이터 로드
        all_data = self.load_monthly_data(crawler_name)
        
        if not all_data:
            self.logger.warning(f"⚠️ No data found for {crawler_name}")
            return False
        
        # 데이터 품질 검증
        quality_issues = self.validate_data_quality(all_data, crawler_name)
        
        # 날짜순 정렬
        all_data.sort(key=lambda x: x.get('date', ''))
        
        # 통계 생성
        stats = self.create_summary_statistics(all_data, crawler_name)
        
        # 통합 파일 저장
        merged_file = self.merged_dir / f"{crawler_name}_merged.json"
        with open(merged_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        # 통계 파일 저장
        stats_file = self.merged_dir / f"{crawler_name}_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        # CSV 파일도 생성 (분석 용이성을 위해)
        try:
            df = pd.DataFrame(all_data)
            csv_file = self.merged_dir / f"{crawler_name}_merged.csv"
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            self.logger.info(f"📊 CSV file created: {csv_file}")
        except Exception as e:
            self.logger.warning(f"CSV creation failed for {crawler_name}: {e}")
        
        self.logger.info(f"✅ {crawler_name} merge completed: {len(all_data)} items → {merged_file}")
        self.logger.info(f"📈 Statistics: {stats['date_statistics']['earliest_date']} ~ {stats['date_statistics']['latest_date']}")
        
        return True
    
    def merge_all_crawlers(self):
        """모든 크롤러 데이터 병합"""
        crawlers = ['yonhap', 'edaily', 'infomax', 'bond', 'interest_rates', 'call_ratings', 'mpb']
        
        self.logger.info(f"🚀 Starting merge for all crawlers: {crawlers}")
        
        success_count = 0
        total_items = 0
        
        for crawler_name in crawlers:
            try:
                success = self.merge_crawler_data(crawler_name)
                if success:
                    success_count += 1
                    
                    # 아이템 수 카운트
                    merged_file = self.merged_dir / f"{crawler_name}_merged.json"
                    if merged_file.exists():
                        with open(merged_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            total_items += len(data)
                            
            except Exception as e:
                self.logger.error(f"Merge failed for {crawler_name}: {e}")
        
        # 전체 요약 보고서 생성
        summary = {
            'merge_completed_at': datetime.now().isoformat(),
            'successful_crawlers': success_count,
            'total_crawlers': len(crawlers),
            'total_items_merged': total_items,
            'output_directory': str(self.merged_dir)
        }
        
        summary_file = self.merged_dir / "merge_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"🎉 Merge completed: {success_count}/{len(crawlers)} crawlers, {total_items:,} total items")
        return summary
    
    def cleanup_monthly_files(self, confirm=False):
        """월별 파일들 정리 (옵션)"""
        if not confirm:
            self.logger.info("⚠️ Use cleanup_monthly_files(confirm=True) to actually delete monthly files")
            return
        
        monthly_files = list(self.monthly_dir.glob("*.json"))
        for file_path in monthly_files:
            file_path.unlink()
        
        self.logger.info(f"🗑️ Cleaned up {len(monthly_files)} monthly files")


if __name__ == "__main__":
    merger = DataMerger()
    
    # 전체 병합 실행
    print("🔄 Starting data merge process...")
    summary = merger.merge_all_crawlers()
    
    print(f"\n📊 MERGE SUMMARY:")
    print(f"✅ Successful: {summary['successful_crawlers']}/{summary['total_crawlers']} crawlers")
    print(f"📈 Total items: {summary['total_items_merged']:,}")
    print(f"📁 Output directory: {summary['output_directory']}")