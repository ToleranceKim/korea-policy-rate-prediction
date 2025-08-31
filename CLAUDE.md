# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository implements a research project for predicting Korean monetary policy directions by analyzing text data from various financial sources. The project reproduces the paper "Deciphering Monetary Policy Board Minutes with Text Mining: The Case of South Korea" and involves crawling, processing, and modeling textual data from:

- Bank of Korea (BOK) Monetary Policy Board minutes
- Financial news articles (Yonhap News, Edaily, InfoMax)
- Bond analysis reports from various securities firms
- Call rate data

The goal is to perform sentiment analysis on financial texts and use machine learning models to predict future interest rate movements.

## Development Environment Setup

### Python Environment
```bash
# Create virtual environment
python -m venv mpb_env
source mpb_env/bin/activate  # On Windows: mpb_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt          # Full dependencies
# OR
pip install -r requirements_core.txt     # Core dependencies only
# OR  
pip install -r requirements_minimal.txt  # Minimal setup
```

### Key Dependencies
- **Web Crawling**: scrapy, requests, beautifulsoup4
- **PDF Processing**: tika, PyPDF2
- **Korean NLP**: ekonlpy, pykospacing
- **Data Processing**: pandas, numpy
- **Machine Learning**: scikit-learn
- **Topic Modeling**: gensim
- **Database**: psycopg2-binary (PostgreSQL), python-dotenv

## Project Architecture

### Data Collection Layer (`/crawler`)
The project implements multiple specialized crawlers:

- **MPB Crawler** (`crawler/MPB/`): Scrapy-based crawler for BOK monetary policy minutes
  - Targets: www.bok.or.kr policy board minutes (PDF format)
  - Extracts: Discussion content and decision results from PDFs
  - Output: JSON format with structured text data
  - **Updated**: 30 pages crawling (optimized from 300 pages)
  - Collection: ~200 documents (2014-2025)

- **News Crawlers** (`crawler/core/base_crawler.py`): 
  - **Yonhap News**: API-based (2016-2025 only), 20s timeout with 3 retries
  - **Edaily**: Direct site crawling, avg 378 articles/month (high variance)
  - **InfoMax**: Direct site crawling, most stable source
  - **Note**: Naver search blocked for Yonhap, use direct methods

- **Bond Reports** (`crawler/BOND/`): Multi-threaded crawler for securities firm reports
  - Targets: finance.naver.com bond analysis reports
  - Processes: PDF extraction using PyPDF2 (Tika deprecated)
  - Period: 2014-08-11 to 2025-08-11
  - Output: CSV files (~5,900 total reports)

- **Supporting Crawlers**:
  - **Call Rates** (`crawler/call_ratings/`): Interest rate data
  - **Interest Rates** (`crawler/interest_rates/`): Historical rate data

### Data Processing Layer (`/preprocess`, `/cleansing`)
- **Text Preprocessing** (`preprocess/`): Tokenization, n-gram analysis
- **Data Cleansing** (`cleansing/`): Data cleaning and normalization
- **N-gram Processing** (`preprocess/ngram/`): Korean text n-gram extraction using eKoNLPy

### Modeling Layer (`/modeling`)
- **NBC (Naive Bayes Classifier)** (`modeling/nbc/`): Sentiment classification
- Uses n-gram features with Korean financial domain-specific preprocessing

### Analysis Layer (`/EDA`)
- **Article Analysis** (`EDA/Article/`): News article visualization
- **MPB Analysis** (`EDA/MPB/`): Word cloud and content analysis

## Common Development Commands

### Running Scrapy Crawlers
```bash
# MPB minutes crawler
cd crawler/MPB
scrapy crawl mpb_crawler -s FEEDS='{"../../data/raw/mpb_minutes.json": {"format": "json"}}'

# Call rates crawler  
cd crawler/call_ratings
scrapy crawl call_ratings -o ../../data/raw/call_rates.csv

# Interest rates crawler
cd crawler/interest_rates  
scrapy crawl interest_rates -o ../../data/raw/interest_rates.csv
```

### Running Bond Reports Crawler
```bash
cd crawler/BOND
python bond_crawling.py
```

### Running Master Crawler Script
```bash
python scripts/paper_reproduction_crawler.py
```

### Data Processing
```bash
# N-gram processing
cd preprocess/ngram
python ngram_dohy.py

# NBC modeling
cd modeling/nbc
python ngram_counter.py
```

### Database Operations
```bash
# Set up environment variables
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# Initialize database schema
psql -U postgres -d mpb_stance_mining -f database/schema.sql

# Run database operations
python database/db_insert_dohy.py
```

## Project Structure Details

### Core Directories
- `/assets/`: Project documentation images
- `/data/`: Raw and processed data storage
- `/scripts/`: Automation and utility scripts
- `/mpb_env/`: Python virtual environment

### Configuration Files
- `scrapy.cfg`: Scrapy project configuration in each crawler directory
- Multiple `requirements*.txt`: Dependency management for different installation levels

### Data Flow
1. **Collection**: Crawlers extract text from various sources
2. **Cleaning**: Text preprocessing and normalization  
3. **Processing**: N-gram extraction and feature engineering
4. **Modeling**: Sentiment analysis and prediction
5. **Storage**: PostgreSQL database insertion and file output

## Korean NLP Considerations

This project uses Korean financial domain-specific NLP:
- **eKoNLPy**: Finance-specialized Korean morphological analyzer
- **Part-of-Speech Tags**: Focus on NNG (nouns), VA (adjectives), MAG (adverbs), VV (verbs), VCN (negative verbs)
- **Text Spacing**: Korean text spacing correction using pykospacing
- **Financial Terminology**: Domain-specific dictionary for financial terms

## Claude Code Usage Guidelines

### Communication Style
- **NO EMOJIS**: Do not use emojis in any communication, logs, comments, or outputs
- **Concise Responses**: Keep responses brief and direct
- **Technical Focus**: Focus on technical implementation without decorative elements
- **Professional Tone**: Maintain a professional, straightforward communication style

## Development Notes

### PDF Processing
- **Current**: PyPDF2 for PDF text extraction (Tika deprecated due to Java dependency)
- **Bond Crawler**: Kospacing disabled (commented out) for text spacing
- Special handling for Korean text in financial documents
- Error handling for corrupted or complex PDF layouts

### Crawler Architecture  
- Mixed implementation: Scrapy for systematic crawling, Jupyter notebooks for ad-hoc analysis
- Multi-threading support in bond reports crawler for performance
- Rate limiting and error handling for web scraping compliance

### Data Storage
- JSON for structured data (MPB minutes, n-gram analysis)
- CSV for tabular data (news articles, financial indicators)
- PostgreSQL database for production storage with:
  - JSONB support for complex Korean text data
  - Full-text search optimized for Korean language
  - Advanced indexing for time-series financial data
  - UPSERT operations for handling data updates

## Important File Locations

- Main crawler implementations: `crawler/*/spiders/*.py`
- Data processing scripts: `preprocess/*.py`, `cleansing/*.py`
- Analysis notebooks: `**/*.ipynb`
- Master automation: `scripts/paper_reproduction_crawler.py`
- Database schemas and scripts: `database/schema.sql`, `database/db_insert_dohy.py`
- Environment configuration: `.env.example` (copy to `.env` for local setup)

## PostgreSQL Database Setup

### Prerequisites
```bash
# Install PostgreSQL (macOS)
brew install postgresql

# Start PostgreSQL service
brew services start postgresql

# Create database
createdb mpb_stance_mining
```

### Database Initialization
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your PostgreSQL credentials
# POSTGRES_PASSWORD=your_password_here

# Initialize schema
psql -U postgres -d mpb_stance_mining -f database/schema.sql
```

### Database Features
- **Korean Text Search**: Full-text search indexes optimized for Korean financial texts
- **JSONB Storage**: Efficient storage for n-gram analysis and model features
- **Time-Series Optimization**: Partitioned tables and indexes for financial time-series data
- **UPSERT Operations**: Handle duplicate data gracefully with ON CONFLICT clauses
- **Performance**: Optimized for large-scale text processing with proper indexing

### Key Tables
- `mpb_minutes`: Bank of Korea meeting minutes
- `news_articles`: Financial news from multiple sources  
- `bond_reports`: Securities firm analysis reports
- `call_rates`: Historical interest rate data
- `processed_texts`: Tokenized and labeled text for ML
- `ngram_analysis`: N-gram features for sentiment analysis
- `predictions`: Final model predictions and accuracy tracking

This project implements a complete pipeline for financial text mining and monetary policy prediction using Korean financial data sources with PostgreSQL as the backbone for efficient text processing and analysis.