#!/usr/bin/env python3
"""
MPB Stance Mining - Main Pipeline Controller
Manages the complete pipeline from data collection to prediction
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from database.db_insert_dohy import PostgreSQLInserter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MPBPipeline:
    """Main pipeline controller for MPB stance mining"""
    
    def __init__(self):
        self.db = None
        
    def __enter__(self):
        try:
            self.db = PostgreSQLInserter()
            logger.info("Database connection established")
        except Exception as e:
            logger.warning(f"Database connection failed: {e}")
            logger.info("Running in file-only mode (data will be saved as JSON/CSV)")
            self.db = None
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            self.db.close()
    
    def run_crawlers(self, sources=None):
        """Run data collection crawlers"""
        logger.info("Starting data collection...")
        
        available_crawlers = {
            'mpb': self._run_mpb_crawler,
            'news': self._run_news_crawlers,
            'bond': self._run_bond_crawler,
            'rates': self._run_rates_crawler
        }
        
        sources = sources or available_crawlers.keys()
        
        for source in sources:
            if source in available_crawlers:
                try:
                    logger.info(f"Running {source} crawler...")
                    available_crawlers[source]()
                    logger.info(f"{source} crawler completed")
                except Exception as e:
                    logger.error(f"{source} crawler failed: {e}")
            else:
                logger.warning(f"Unknown crawler: {source}")
    
    def _run_mpb_crawler(self):
        """Run MPB minutes crawler"""
        logger.info("Running MPB minutes crawler...")
        
        try:
            import subprocess
            
            # Change to MPB crawler directory
            mpb_crawler_path = project_root / "crawler" / "MPB" / "mpb_crawler"
            
            if not mpb_crawler_path.exists():
                raise FileNotFoundError(f"MPB crawler directory not found: {mpb_crawler_path}")
            
            # Run Scrapy crawler
            result = subprocess.run(
                ["scrapy", "crawl", "mpb_crawler", "-o", "mpb_output.json"],
                cwd=str(mpb_crawler_path),
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info("MPB crawler completed successfully")
                
                # Process the output file and store in database
                output_file = mpb_crawler_path / "mpb_output.json"
                if output_file.exists():
                    if self.db:
                        self._process_mpb_data(str(output_file))
                    else:
                        logger.info(f"MPB data saved to: {output_file}")
                else:
                    logger.warning("MPB output file not found")
            else:
                logger.error(f"MPB crawler failed: {result.stderr}")
                raise Exception(f"MPB crawler process failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("MPB crawler timed out")
            raise
        except Exception as e:
            logger.error(f"Failed to run MPB crawler: {e}")
            raise
    
    def _run_news_crawlers(self):
        """Run news crawlers"""
        logger.info("Running news crawlers...")
        
        try:
            import subprocess
            
            crawlers = [
                {
                    'name': 'Yonhap News',
                    'path': project_root / "crawler" / "yh" / "yh_crawler" / "yh_crawler",
                    'spider': 'yh_spider',
                    'output': 'yh_output.json'
                },
                {
                    'name': 'Edaily',
                    'path': project_root / "crawler" / "edaily" / "edaily_crawler" / "edaily_crawler",
                    'spider': 'edaily_spider', 
                    'output': 'edaily_output.json'
                }
            ]
            
            for crawler in crawlers:
                try:
                    if not crawler['path'].exists():
                        logger.warning(f"{crawler['name']} crawler directory not found: {crawler['path']}")
                        continue
                    
                    logger.info(f"Running {crawler['name']} crawler...")
                    
                    # Run Scrapy crawler
                    result = subprocess.run(
                        ["scrapy", "crawl", crawler['spider'], "-o", crawler['output']],
                        cwd=str(crawler['path']),
                        capture_output=True,
                        text=True,
                        timeout=1800  # 30 minutes timeout
                    )
                    
                    if result.returncode == 0:
                        logger.info(f"{crawler['name']} crawler completed successfully")
                        
                        # Process the output file and store in database
                        output_file = crawler['path'] / crawler['output']
                        if output_file.exists():
                            if self.db:
                                self._process_news_data(str(output_file), crawler['name'].lower())
                            else:
                                logger.info(f"{crawler['name']} data saved to: {output_file}")
                        else:
                            logger.warning(f"{crawler['name']} output file not found")
                    else:
                        logger.error(f"{crawler['name']} crawler failed: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    logger.error(f"{crawler['name']} crawler timed out")
                except Exception as e:
                    logger.error(f"Failed to run {crawler['name']} crawler: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to run news crawlers: {e}") 
            raise
    
    def _run_bond_crawler(self):
        """Run bond reports crawler"""
        logger.info("Running bond reports crawler...")
        
        try:
            import subprocess
            import sys
            
            # Change to BOND crawler directory
            bond_crawler_path = project_root / "crawler" / "BOND"
            bond_script = bond_crawler_path / "bond_crawling.py"
            
            if not bond_script.exists():
                raise FileNotFoundError(f"Bond crawler script not found: {bond_script}")
            
            # Run the bond crawling script
            result = subprocess.run(
                [sys.executable, str(bond_script)],
                cwd=str(bond_crawler_path),
                capture_output=True,
                text=True,
                timeout=3600  # 60 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info("Bond crawler completed successfully")
                
                # Process the CSV files generated in dataset_2 directory
                dataset_path = bond_crawler_path / "dataset_2"
                if dataset_path.exists():
                    if self.db:
                        self._process_bond_data(str(dataset_path))
                    else:
                        logger.info(f"Bond data saved to: {dataset_path}")
                else:
                    logger.warning("Bond dataset directory not found")
            else:
                logger.error(f"Bond crawler failed: {result.stderr}")
                logger.error(f"Bond crawler stdout: {result.stdout}")
                raise Exception(f"Bond crawler process failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("Bond crawler timed out")
            raise
        except Exception as e:
            logger.error(f"Failed to run bond crawler: {e}")
            raise
    
    def _run_rates_crawler(self):
        """Run call rates crawler"""
        logger.info("Running call rates crawler...")
        
        try:
            import subprocess
            
            # Change to call ratings crawler directory
            rates_crawler_path = project_root / "crawler" / "call_ratings" / "call_ratings_crawler"
            
            if not rates_crawler_path.exists():
                raise FileNotFoundError(f"Call rates crawler directory not found: {rates_crawler_path}")
            
            # Run Scrapy crawler
            result = subprocess.run(
                ["scrapy", "crawl", "call_ratings", "-o", "call_rates_output.json"],
                cwd=str(rates_crawler_path),
                capture_output=True,
                text=True,
                timeout=900  # 15 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info("Call rates crawler completed successfully")
                
                # Process the output file and store in database
                output_file = rates_crawler_path / "call_rates_output.json"
                if output_file.exists():
                    if self.db:
                        self._process_rates_data(str(output_file))
                    else:
                        logger.info(f"Call rates data saved to: {output_file}")
                else:
                    logger.warning("Call rates output file not found")
            else:
                logger.error(f"Call rates crawler failed: {result.stderr}")
                raise Exception(f"Call rates crawler process failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("Call rates crawler timed out")
            raise
        except Exception as e:
            logger.error(f"Failed to run call rates crawler: {e}")
            raise
    
    def process_data(self):
        """Process and clean collected data"""
        logger.info("🧹 Starting data processing...")
        
        try:
            # Check data availability
            stats = self._get_data_stats()
            logger.info(f"Data available: {stats}")
            
            # Process text data
            self._clean_text_data()
            self._tokenize_texts()
            self._label_data()
            
            logger.info("Data processing completed")
            
        except Exception as e:
            logger.error(f"Data processing failed: {e}")
            raise
    
    def _get_data_stats(self):
        """Get statistics of collected data"""
        if not self.db:
            logger.info("Database not available, checking file outputs...")
            return self._get_file_stats()
        
        stats = {}
        tables = ['mpb_minutes', 'news_articles', 'bond_reports', 'call_rates']
        
        for table in tables:
            try:
                result = self.db.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                stats[table] = result[0]['count'] if result else 0
            except:
                stats[table] = 0
        
        return stats
    
    def _get_file_stats(self):
        """Get statistics from output files when database is not available"""
        stats = {}
        
        # Check MPB output
        mpb_file = project_root / "crawler" / "MPB" / "mpb_crawler" / "mpb_output.json"
        stats['mpb_minutes'] = self._count_json_records(mpb_file)
        
        # Check news outputs
        yh_file = project_root / "crawler" / "yh" / "yh_crawler" / "yh_crawler" / "yh_output.json"
        edaily_file = project_root / "crawler" / "edaily" / "edaily_crawler" / "edaily_crawler" / "edaily_output.json"
        stats['news_articles'] = self._count_json_records(yh_file) + self._count_json_records(edaily_file)
        
        # Check bond outputs
        bond_dir = project_root / "crawler" / "BOND" / "dataset_2"
        stats['bond_reports'] = self._count_csv_files(bond_dir)
        
        # Check rates output
        rates_file = project_root / "crawler" / "call_ratings" / "call_ratings_crawler" / "call_rates_output.json"
        stats['call_rates'] = self._count_json_records(rates_file)
        
        return stats
    
    def _count_json_records(self, file_path):
        """Count records in JSON file"""
        try:
            if file_path.exists():
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return len(data) if isinstance(data, list) else 1
        except:
            pass
        return 0
    
    def _count_csv_files(self, dir_path):
        """Count CSV files in directory"""
        try:
            if dir_path.exists():
                return len([f for f in dir_path.glob('*.csv')])
        except:
            pass
        return 0
    
    def _clean_text_data(self):
        """Clean and normalize text data"""
        logger.info("Cleaning text data...")
        # TODO: Implement text cleaning logic
        pass
    
    def _tokenize_texts(self):
        """Tokenize texts using Korean NLP"""
        logger.info("Tokenizing texts...")
        # TODO: Implement tokenization logic
        pass
    
    def _label_data(self):
        """Label data based on rate changes"""
        logger.info("Labeling data...")
        # TODO: Implement labeling logic
        pass
    
    def analyze_ngrams(self):
        """Perform n-gram analysis"""
        logger.info("Starting n-gram analysis...")
        
        try:
            # Perform n-gram extraction for different sizes
            for n in range(1, 6):
                logger.info(f"Extracting {n}-grams...")
                self._extract_ngrams(n)
            
            logger.info("N-gram analysis completed")
            
        except Exception as e:
            logger.error(f"N-gram analysis failed: {e}")
            raise
    
    def _extract_ngrams(self, n):
        """Extract n-grams of size n"""
        # TODO: Implement n-gram extraction
        logger.debug(f"Processing {n}-grams")
        pass
    
    def train_models(self):
        """Train prediction models"""
        logger.info("Starting model training...")
        
        try:
            # Train different models
            models = ['nbc', 'svm', 'deep_learning']
            
            for model_type in models:
                logger.info(f"Training {model_type} model...")
                self._train_model(model_type)
            
            logger.info("Model training completed")
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            raise
    
    def _train_model(self, model_type):
        """Train specific model type"""
        # TODO: Implement model training
        logger.debug(f"Training {model_type} model")
        pass
    
    def evaluate_models(self):
        """Evaluate model performance"""
        logger.info("Starting model evaluation...")
        
        try:
            # Evaluate models
            results = self._run_evaluation()
            
            # Log results
            for model, metrics in results.items():
                logger.info(f"{model}: {metrics}")
            
            logger.info("Model evaluation completed")
            return results
            
        except Exception as e:
            logger.error(f"Model evaluation failed: {e}")
            raise
    
    def _run_evaluation(self):
        """Run model evaluation"""
        # TODO: Implement model evaluation
        return {}
    
    def generate_predictions(self, target_date=None):
        """Generate predictions for future rate changes"""
        logger.info("Generating predictions...")
        
        try:
            if not target_date:
                # Default to 2 months from now
                from datetime import datetime, timedelta
                target_date = datetime.now() + timedelta(days=60)
            
            # Generate predictions using ensemble of models
            prediction = self._predict_rate_change(target_date)
            
            # Store prediction in database
            self._store_prediction(prediction, target_date)
            
            logger.info(f"Prediction generated for {target_date}")
            return prediction
            
        except Exception as e:
            logger.error(f"Prediction generation failed: {e}")
            raise
    
    def _predict_rate_change(self, target_date):
        """Predict rate change for target date"""
        # TODO: Implement prediction logic
        logger.debug(f"Predicting for {target_date}")
        return {'direction': 1, 'confidence': 0.75}
    
    def _store_prediction(self, prediction, target_date):
        """Store prediction in database"""
        # TODO: Implement prediction storage
        logger.debug(f"Storing prediction {prediction} for {target_date}")
        pass
    
    def _process_mpb_data(self, output_file):
        """Process MPB crawler output and store in database"""
        logger.info(f"Processing MPB data from {output_file}")
        
        try:
            import json
            from datetime import datetime
            
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get MPB source ID
            mpb_source = self.db.execute_query(
                "SELECT id FROM data_sources WHERE source_code = %s", ('mpb',)
            )
            source_id = mpb_source[0]['id'] if mpb_source else 1
            
            inserted_count = 0
            for item in data:
                try:
                    # Parse date
                    date_str = item.get('date')
                    if date_str:
                        # Convert Korean date format to standard date
                        date_obj = datetime.strptime(date_str, '%Y.%m.%d').date()
                    else:
                        continue
                    
                    # Check if already exists
                    existing = self.db.execute_query(
                        "SELECT id FROM mpb_minutes WHERE date = %s AND title = %s",
                        (date_obj, item.get('title', ''))
                    )
                    
                    if not existing:
                        data_dict = {
                            'date': date_obj,
                            'title': item.get('title', ''),
                            'content': item.get('content', ''),
                            'discussion': item.get('discussion', ''),
                            'decision': item.get('decision', ''),
                            'link': item.get('link', ''),
                            'source_id': source_id
                        }
                        
                        self.db.insert_one('mpb_minutes', data_dict)
                        inserted_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to process MPB item {item}: {e}")
                    continue
            
            logger.info(f"Inserted {inserted_count} new MPB minutes records")
            
        except Exception as e:
            logger.error(f"Failed to process MPB data: {e}")
            raise
    
    def _process_bond_data(self, dataset_path):
        """Process bond crawler CSV output and store in database"""
        logger.info(f"Processing bond data from {dataset_path}")
        
        try:
            import csv
            import os
            from datetime import datetime
            
            # Get bond source ID
            bond_source = self.db.execute_query(
                "SELECT id FROM data_sources WHERE source_code = %s", ('bond',)
            )
            source_id = bond_source[0]['id'] if bond_source else 5
            
            inserted_count = 0
            
            # Process all CSV files in the dataset directory
            for filename in os.listdir(dataset_path):
                if filename.endswith('.csv'):
                    csv_path = os.path.join(dataset_path, filename)
                    
                    try:
                        with open(csv_path, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                try:
                                    # Parse date from filename or content
                                    date_str = row.get('Date', '')
                                    if date_str:
                                        date_obj = datetime.strptime(date_str, '%Y.%m.%d').date()
                                    else:
                                        # Try to parse from filename
                                        date_part = filename.split('_')[0]
                                        date_obj = datetime.strptime(date_part, '%Y.%m.%d').date()
                                    
                                    # Check if already exists
                                    existing = self.db.execute_query(
                                        "SELECT id FROM bond_reports WHERE date = %s AND title = %s",
                                        (date_obj, row.get('Title', ''))
                                    )
                                    
                                    if not existing:
                                        data_dict = {
                                            'date': date_obj,
                                            'title': row.get('Title', ''),
                                            'content': row.get('Content', ''),
                                            'link': row.get('Link', ''),
                                            'source_id': source_id,
                                            'report_type': 'bond_analysis'
                                        }
                                        
                                        self.db.insert_one('bond_reports', data_dict)
                                        inserted_count += 1
                                        
                                except Exception as e:
                                    logger.error(f"Failed to process bond CSV row {row}: {e}")
                                    continue
                                    
                    except Exception as e:
                        logger.error(f"Failed to process bond CSV file {csv_path}: {e}")
                        continue
            
            logger.info(f"Inserted {inserted_count} new bond reports records")
            
        except Exception as e:
            logger.error(f"Failed to process bond data: {e}")
            raise
    
    def _process_rates_data(self, output_file):
        """Process call rates crawler output and store in database"""
        logger.info(f"Processing call rates data from {output_file}")
        
        try:
            import json
            from datetime import datetime
            
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            inserted_count = 0
            for item in data:
                try:
                    # Parse date
                    date_str = item.get('날짜', '')  # Korean for 'date'
                    if date_str:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    else:
                        continue
                    
                    # Parse call rate
                    call_rate_str = item.get('콜금리', '')  # Korean for 'call rate'
                    if call_rate_str:
                        call_rate = float(call_rate_str)
                    else:
                        continue
                    
                    # Check if already exists
                    existing = self.db.execute_query(
                        "SELECT id FROM call_rates WHERE date = %s", (date_obj,)
                    )
                    
                    if not existing:
                        data_dict = {
                            'date': date_obj,
                            'call_rate': call_rate
                        }
                        
                        self.db.insert_one('call_rates', data_dict)
                        inserted_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to process rates item {item}: {e}")
                    continue
            
            logger.info(f"Inserted {inserted_count} new call rates records")
            
        except Exception as e:
            logger.error(f"Failed to process call rates data: {e}")
            raise
    
    def _process_news_data(self, output_file, source_name):
        """Process news crawler output and store in database"""
        logger.info(f"Processing {source_name} news data from {output_file}")
        
        try:
            import json
            from datetime import datetime
            
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get source ID based on source name
            source_mapping = {
                'yonhap news': 'yh',
                'edaily': 'edaily'
            }
            
            source_code = source_mapping.get(source_name, source_name)
            source_result = self.db.execute_query(
                "SELECT id FROM data_sources WHERE source_code = %s", (source_code,)
            )
            source_id = source_result[0]['id'] if source_result else None
            
            if not source_id:
                logger.warning(f"Source ID not found for {source_name}, skipping")
                return
            
            inserted_count = 0
            for item in data:
                try:
                    # Parse date
                    date_str = item.get('date', '')
                    if date_str:
                        if isinstance(date_str, str):
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                        else:
                            continue
                    else:
                        continue
                    
                    # Check if already exists
                    existing = self.db.execute_query(
                        "SELECT id FROM news_articles WHERE date = %s AND title = %s AND source_id = %s",
                        (date_obj, item.get('title', ''), source_id)
                    )
                    
                    if not existing:
                        data_dict = {
                            'date': date_obj,
                            'title': item.get('title', ''),
                            'content': item.get('content', ''),
                            'link': item.get('link', ''),
                            'source_id': source_id,
                            'author': item.get('author', '')
                        }
                        
                        self.db.insert_one('news_articles', data_dict)
                        inserted_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to process {source_name} news item {item}: {e}")
                    continue
            
            logger.info(f"Inserted {inserted_count} new {source_name} news articles")
            
        except Exception as e:
            logger.error(f"Failed to process {source_name} news data: {e}")
            raise
    
    def run_full_pipeline(self):
        """Run the complete pipeline"""
        logger.info("Starting full MPB stance mining pipeline...")
        
        try:
            # Step 1: Data Collection
            self.run_crawlers()
            
            # Step 2: Data Processing
            self.process_data()
            
            # Step 3: N-gram Analysis
            self.analyze_ngrams()
            
            # Step 4: Model Training
            self.train_models()
            
            # Step 5: Model Evaluation
            results = self.evaluate_models()
            
            # Step 6: Generate Predictions
            prediction = self.generate_predictions()
            
            logger.info("Full pipeline completed successfully!")
            logger.info(f"Final prediction: {prediction}")
            
            return {
                'evaluation_results': results,
                'prediction': prediction,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='MPB Stance Mining Pipeline')
    
    parser.add_argument('--stage', choices=['crawl', 'process', 'ngram', 'train', 'evaluate', 'predict', 'full'],
                        default='full', help='Pipeline stage to run')
    parser.add_argument('--sources', nargs='+', choices=['mpb', 'news', 'bond', 'rates'],
                        help='Data sources for crawling')
    parser.add_argument('--target-date', type=str, help='Target date for prediction (YYYY-MM-DD)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Convert target date if provided
    target_date = None
    if args.target_date:
        target_date = datetime.strptime(args.target_date, '%Y-%m-%d')
    
    # Run pipeline
    with MPBPipeline() as pipeline:
        if args.stage == 'crawl':
            pipeline.run_crawlers(args.sources)
        elif args.stage == 'process':
            pipeline.process_data()
        elif args.stage == 'ngram':
            pipeline.analyze_ngrams()
        elif args.stage == 'train':
            pipeline.train_models()
        elif args.stage == 'evaluate':
            pipeline.evaluate_models()
        elif args.stage == 'predict':
            pipeline.generate_predictions(target_date)
        elif args.stage == 'full':
            result = pipeline.run_full_pipeline()
            if result['status'] == 'failed':
                sys.exit(1)

if __name__ == "__main__":
    main()