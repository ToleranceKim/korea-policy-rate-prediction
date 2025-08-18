#!/usr/bin/env python3
"""
프로젝트 정리 후 경로 오류 수정 스크립트
"""

import re
from pathlib import Path
import logging

class PathFixer:
    def __init__(self, base_dir="/Users/lord_jubin/Desktop/my_git/mpb-stance-mining/crawler"):
        self.base_dir = Path(base_dir)
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def fix_batch_collector(self):
        """BatchCollector 경로 수정"""
        file_path = self.base_dir / "scripts" / "batch" / "batch_collector.py"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 경로 수정
        content = content.replace(
            'self.output_dir = self.base_dir / "monthly_output"',
            'self.output_dir = self.base_dir / "data" / "monthly"'
        )
        
        content = content.replace(
            'logging.FileHandler(self.base_dir / "batch_collector.log")',
            'logging.FileHandler(self.base_dir / "logs" / "batch_collector.log")'
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info("✅ Fixed BatchCollector paths")
    
    def fix_data_merger(self):
        """DataMerger 경로 수정"""
        file_path = self.base_dir / "scripts" / "batch" / "data_merger.py"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 경로 수정
        content = content.replace(
            'self.monthly_dir = self.base_dir / "monthly_output"',
            'self.monthly_dir = self.base_dir / "data" / "monthly"'
        )
        
        content = content.replace(
            'self.merged_dir = self.base_dir / "merged_output"',
            'self.merged_dir = self.base_dir / "data" / "merged"'
        )
        
        content = content.replace(
            'logging.FileHandler(self.base_dir / "data_merger.log")',
            'logging.FileHandler(self.base_dir / "logs" / "data_merger.log")'
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info("✅ Fixed DataMerger paths")
    
    def create_new_run_script(self):
        """새로운 실행 스크립트 생성 (크롤러 루트에)"""
        new_script_path = self.base_dir / "run_batch_collection.py"
        
        content = '''#!/usr/bin/env python3
"""
월별 분할 수집 실행 스크립트 (경로 수정됨)
"""

import sys
import argparse
from pathlib import Path

# scripts/batch 디렉터리를 경로에 추가
sys.path.append(str(Path(__file__).parent / "scripts" / "batch"))

from batch_collector import BatchCollector
from data_merger import DataMerger

def main():
    parser = argparse.ArgumentParser(description='월별 분할 데이터 수집 시스템')
    parser.add_argument('--crawlers', nargs='+', 
                        choices=['yonhap', 'edaily', 'infomax', 'bond', 'interest_rates', 'call_ratings', 'mpb'],
                        default=['yonhap', 'edaily', 'infomax'],
                        help='수집할 크롤러 선택')
    parser.add_argument('--test', action='store_true', help='테스트 모드 (소량 수집)')
    parser.add_argument('--resume', type=str, help='특정 월부터 재시작 (YYYY-MM 형식)')
    parser.add_argument('--merge-only', action='store_true', help='수집 없이 병합만 실행')
    parser.add_argument('--status', action='store_true', help='현재 상태만 확인')
    
    args = parser.parse_args()
    
    collector = BatchCollector()
    
    if args.status:
        collector.print_status()
        return
    
    if args.merge_only:
        print("🔄 Starting merge-only process...")
        merger = DataMerger()
        merger.merge_all_crawlers()
        return
    
    print(f"🚀 Starting batch collection...")
    print(f"📋 Target crawlers: {args.crawlers}")
    
    if args.test:
        print("🧪 TEST MODE: Limited collection for validation")
        # 테스트 모드에서는 최근 1개월만 수집
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # 테스트용 수동 수집
        for crawler_name in args.crawlers:
            if crawler_name in ['yonhap', 'edaily', 'infomax']:
                test_period = {
                    'key': 'test',
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                }
                config = collector.crawlers[crawler_name]
                collector.collect_monthly_news(crawler_name, config, test_period)
    else:
        # 전체 월별 수집
        collector.run_monthly_collection(args.crawlers, args.resume)
    
    # 수집 완료 후 상태 출력
    print("\\n" + "="*60)
    collector.print_status()
    
    # 병합 실행 여부 확인
    try:
        if input("\\n🔄 수집된 데이터를 병합하시겠습니까? (y/N): ").lower() == 'y':
            merger = DataMerger()
            merger.merge_all_crawlers()
    except (EOFError, KeyboardInterrupt):
        print("\\nSkipping merge step...")

if __name__ == "__main__":
    main()
'''
        
        with open(new_script_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 실행 권한 부여
        new_script_path.chmod(0o755)
        
        self.logger.info("✅ Created new run_batch_collection.py in crawler root")
    
    def verify_imports(self):
        """임포트 경로 확인"""
        script_path = self.base_dir / "run_batch_collection.py"
        
        try:
            # 테스트용 임포트
            import sys
            sys.path.append(str(self.base_dir / "scripts" / "batch"))
            
            from batch_collector import BatchCollector
            from data_merger import DataMerger
            
            # 간단한 인스턴스 생성 테스트
            collector = BatchCollector()
            merger = DataMerger()
            
            self.logger.info("✅ Import verification successful")
            return True
            
        except ImportError as e:
            self.logger.error(f"❌ Import error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Other error: {e}")
            return False
    
    def check_directory_structure(self):
        """디렉터리 구조 확인"""
        required_dirs = [
            self.base_dir / "data" / "monthly",
            self.base_dir / "data" / "merged",
            self.base_dir / "logs",
            self.base_dir / "scripts" / "batch"
        ]
        
        all_exist = True
        for directory in required_dirs:
            if directory.exists():
                self.logger.info(f"✅ Directory exists: {directory.name}")
            else:
                self.logger.error(f"❌ Missing directory: {directory}")
                all_exist = False
        
        return all_exist
    
    def run_fixes(self):
        """모든 경로 수정 실행"""
        self.logger.info("🔧 Starting path fixes...")
        
        # 1. 디렉터리 구조 확인
        if not self.check_directory_structure():
            self.logger.error("Directory structure issues detected!")
            return False
        
        # 2. 스크립트 경로 수정
        self.fix_batch_collector()
        self.fix_data_merger()
        
        # 3. 새로운 실행 스크립트 생성
        self.create_new_run_script()
        
        # 4. 임포트 확인
        if self.verify_imports():
            self.logger.info("🎉 All path fixes completed successfully!")
            return True
        else:
            self.logger.error("❌ Path fixes failed verification")
            return False

if __name__ == "__main__":
    fixer = PathFixer()
    success = fixer.run_fixes()
    
    if success:
        print("\\n" + "="*60)
        print("✅ PATH FIXES COMPLETED")
        print("="*60)
        print("📁 Updated paths:")
        print("  - monthly data: crawler/data/monthly/")
        print("  - merged data: crawler/data/merged/")
        print("  - logs: crawler/logs/")
        print("  - scripts: crawler/scripts/batch/")
        print("")
        print("🚀 Usage:")
        print("  python run_batch_collection.py --status")
        print("  python run_batch_collection.py --test")
        print("="*60)
    else:
        print("❌ Path fixes failed. Please check the logs.")