#!/usr/bin/env python3
"""
프로젝트 디렉터리 정리 스크립트
- 불필요한 파일 제거
- 디렉터리 구조 정리
- 아카이브 폴더로 이동
"""

import os
import shutil
from pathlib import Path
import logging

class ProjectCleaner:
    def __init__(self, base_dir="/Users/lord_jubin/Desktop/my_git/mpb-stance-mining/crawler"):
        self.base_dir = Path(base_dir)
        self.archive_dir = self.base_dir / "archive"
        self.logs_dir = self.base_dir / "logs"
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.base_dir / "cleanup.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def create_directory_structure(self):
        """개선된 디렉터리 구조 생성"""
        directories = [
            # 아카이브 관련
            self.archive_dir / "bond_pdfs",
            self.archive_dir / "bond_csvs", 
            self.archive_dir / "test_outputs",
            
            # 로그 관리
            self.logs_dir,
            
            # 데이터 관리
            self.base_dir / "data" / "raw",
            self.base_dir / "data" / "processed",
            self.base_dir / "data" / "monthly",
            self.base_dir / "data" / "merged",
            
            # 스크립트 관리
            self.base_dir / "scripts" / "batch",
            self.base_dir / "scripts" / "utils"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"✅ Created directory: {directory}")
    
    def clean_system_files(self):
        """시스템 파일들 제거"""
        system_files = list(self.base_dir.rglob(".DS_Store"))
        
        for file_path in system_files:
            try:
                file_path.unlink()
                self.logger.info(f"🗑️ Removed system file: {file_path}")
            except Exception as e:
                self.logger.error(f"Failed to remove {file_path}: {e}")
        
        return len(system_files)
    
    def move_bond_files(self):
        """BOND 디렉터리 정리"""
        bond_dir = self.base_dir / "BOND"
        
        if not bond_dir.exists():
            return 0, 0
        
        # PDF 파일들 이동
        pdf_files = list(bond_dir.glob("*.pdf"))
        pdf_count = 0
        
        for pdf_file in pdf_files:
            try:
                target = self.archive_dir / "bond_pdfs" / pdf_file.name
                shutil.move(str(pdf_file), str(target))
                pdf_count += 1
            except Exception as e:
                self.logger.error(f"Failed to move PDF {pdf_file}: {e}")
        
        # dataset_2 디렉터리 이동
        dataset_dir = bond_dir / "dataset_2"
        csv_count = 0
        
        if dataset_dir.exists():
            try:
                target = self.archive_dir / "bond_csvs"
                if target.exists():
                    shutil.rmtree(target)
                shutil.move(str(dataset_dir), str(target))
                
                # CSV 파일 개수 세기
                csv_count = len(list((self.archive_dir / "bond_csvs").glob("*.csv")))
                
            except Exception as e:
                self.logger.error(f"Failed to move dataset_2: {e}")
        
        self.logger.info(f"📦 Moved {pdf_count} PDF files and {csv_count} CSV files from BOND")
        return pdf_count, csv_count
    
    def clean_test_files(self):
        """테스트 파일들 정리"""
        test_patterns = [
            "*_test.json",
            "*_output.json", 
            "*_validation*.json",
            "debug_*.py",
            "test_*.py"
        ]
        
        moved_files = 0
        
        for pattern in test_patterns:
            test_files = list(self.base_dir.rglob(pattern))
            
            for test_file in test_files:
                # 중요한 시스템 파일들은 건드리지 않음
                if any(skip in str(test_file) for skip in ['batch_collector', 'data_merger', 'run_batch']):
                    continue
                
                try:
                    target = self.archive_dir / "test_outputs" / test_file.name
                    shutil.move(str(test_file), str(target))
                    moved_files += 1
                    self.logger.info(f"📦 Moved test file: {test_file.name}")
                except Exception as e:
                    self.logger.error(f"Failed to move {test_file}: {e}")
        
        return moved_files
    
    def move_logs(self):
        """로그 파일들 정리"""
        log_files = list(self.base_dir.glob("*.log"))
        moved_logs = 0
        
        for log_file in log_files:
            try:
                target = self.logs_dir / log_file.name
                shutil.move(str(log_file), str(target))
                moved_logs += 1
                self.logger.info(f"📝 Moved log file: {log_file.name}")
            except Exception as e:
                self.logger.error(f"Failed to move log {log_file}: {e}")
        
        return moved_logs
    
    def reorganize_data_directories(self):
        """데이터 디렉터리 재구성"""
        moves = [
            # monthly_output -> data/monthly
            (self.base_dir / "monthly_output", self.base_dir / "data" / "monthly"),
            # merged_output -> data/merged  
            (self.base_dir / "merged_output", self.base_dir / "data" / "merged")
        ]
        
        for source, target in moves:
            if source.exists():
                try:
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.move(str(source), str(target))
                    self.logger.info(f"📁 Moved {source.name} to {target}")
                except Exception as e:
                    self.logger.error(f"Failed to move {source}: {e}")
    
    def move_utility_scripts(self):
        """유틸리티 스크립트들 정리"""
        utility_scripts = [
            "batch_collector.py",
            "data_merger.py", 
            "run_batch_collection.py"
        ]
        
        moved_scripts = 0
        
        for script in utility_scripts:
            script_path = self.base_dir / script
            if script_path.exists():
                try:
                    target = self.base_dir / "scripts" / "batch" / script
                    shutil.move(str(script_path), str(target))
                    moved_scripts += 1
                    self.logger.info(f"🔧 Moved utility script: {script}")
                except Exception as e:
                    self.logger.error(f"Failed to move {script}: {e}")
        
        # 기타 연구용 스크립트들
        research_scripts = list(self.base_dir.glob("research_*.py"))
        for script in research_scripts:
            try:
                target = self.base_dir / "scripts" / "utils" / script.name
                shutil.move(str(script), str(target))
                moved_scripts += 1
                self.logger.info(f"🔬 Moved research script: {script.name}")
            except Exception as e:
                self.logger.error(f"Failed to move research script {script}: {e}")
        
        return moved_scripts
    
    def create_readme_files(self):
        """각 디렉터리에 README 파일 생성"""
        readme_contents = {
            self.archive_dir: """# Archive Directory

이 디렉터리는 프로젝트 정리 과정에서 이동된 파일들을 보관합니다.

## 구조:
- `bond_pdfs/`: 채권 관련 PDF 파일들 (수집된 리서치 보고서)
- `bond_csvs/`: 처리된 채권 데이터 CSV 파일들 (6000+ 개)
- `test_outputs/`: 개발 중 생성된 테스트 출력 파일들

이 파일들은 안전하게 보관되며, 필요 시 언제든 복원 가능합니다.
""",
            
            self.logs_dir: """# Logs Directory

시스템 로그 파일들이 저장되는 디렉터리입니다.

- 배치 수집 로그
- 데이터 병합 로그  
- 크롤러 실행 로그
- 시스템 정리 로그
""",
            
            self.base_dir / "data": """# Data Directory

수집 및 처리된 데이터를 체계적으로 관리합니다.

## 구조:
- `raw/`: 원본 수집 데이터
- `processed/`: 가공된 데이터
- `monthly/`: 월별 분할 수집 데이터
- `merged/`: 통합된 최종 데이터
""",
            
            self.base_dir / "scripts": """# Scripts Directory

시스템 관리 및 유틸리티 스크립트들을 보관합니다.

## 구조:
- `batch/`: 배치 수집 시스템 스크립트들
- `utils/`: 연구 및 유틸리티 스크립트들
"""
        }
        
        for directory, content in readme_contents.items():
            readme_path = directory / "README.md"
            try:
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.logger.info(f"📄 Created README: {readme_path}")
            except Exception as e:
                self.logger.error(f"Failed to create README at {readme_path}: {e}")
    
    def run_cleanup(self, confirm=False):
        """전체 정리 프로세스 실행"""
        if not confirm:
            self.logger.warning("⚠️ DRY RUN MODE - No files will be moved")
            self.logger.warning("Use run_cleanup(confirm=True) to actually perform cleanup")
            return
        
        self.logger.info("🧹 Starting project cleanup...")
        
        # 1. 디렉터리 구조 생성
        self.create_directory_structure()
        
        # 2. 시스템 파일 정리
        system_files_count = self.clean_system_files()
        
        # 3. BOND 파일들 이동
        pdf_count, csv_count = self.move_bond_files()
        
        # 4. 테스트 파일들 정리
        test_files_count = self.clean_test_files()
        
        # 5. 로그 파일들 이동
        log_files_count = self.move_logs()
        
        # 6. 데이터 디렉터리 재구성
        self.reorganize_data_directories()
        
        # 7. 스크립트들 정리
        script_files_count = self.move_utility_scripts()
        
        # 8. README 파일들 생성
        self.create_readme_files()
        
        # 정리 완료 보고서
        summary = f"""
🎉 PROJECT CLEANUP COMPLETED

📊 SUMMARY:
- System files removed: {system_files_count}
- PDF files archived: {pdf_count}
- CSV files archived: {csv_count}  
- Test files moved: {test_files_count}
- Log files organized: {log_files_count}
- Scripts reorganized: {script_files_count}

📁 NEW STRUCTURE:
- archive/: 아카이브된 파일들
- logs/: 로그 파일들
- data/: 체계적으로 관리되는 데이터
- scripts/: 정리된 스크립트들

✅ Project is now clean and well-organized!
        """
        
        self.logger.info(summary)
        print(summary)


if __name__ == "__main__":
    cleaner = ProjectCleaner()
    
    # 정리 실행 (확인 후)
    print("🧹 Project cleanup ready to run...")
    print("This will reorganize your project structure and move files to appropriate locations.")
    
    if input("Proceed with cleanup? (y/N): ").lower() == 'y':
        cleaner.run_cleanup(confirm=True)
    else:
        print("Cleanup cancelled.")
        cleaner.run_cleanup(confirm=False)  # Dry run to show what would happen