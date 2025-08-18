-- MPB Stance Mining Database Schema for PostgreSQL
-- This schema is optimized for Korean text processing and financial data analysis

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Drop existing tables if they exist (for development)
DROP TABLE IF EXISTS predictions CASCADE;
DROP TABLE IF EXISTS model_results CASCADE;
DROP TABLE IF EXISTS ngram_analysis CASCADE;
DROP TABLE IF EXISTS processed_texts CASCADE;
DROP TABLE IF EXISTS call_rates CASCADE;
DROP TABLE IF EXISTS bond_reports CASCADE;
DROP TABLE IF EXISTS news_articles CASCADE;
DROP TABLE IF EXISTS mpb_minutes CASCADE;
DROP TABLE IF EXISTS data_sources CASCADE;

-- Data sources lookup table
CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) UNIQUE NOT NULL,
    source_code VARCHAR(10) UNIQUE NOT NULL,
    description TEXT,
    base_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default data sources
INSERT INTO data_sources (source_name, source_code, description, base_url) VALUES
('Monetary Policy Board', 'mpb', 'Bank of Korea Monetary Policy Board Minutes', 'https://www.bok.or.kr'),
('Yonhap News', 'yh', 'Yonhap News Agency Financial News', 'https://www.yna.co.kr'),
('Edaily', 'edaily', 'Edaily Financial News', 'https://www.edaily.co.kr'),
('InfoMax', 'infomax', 'InfoMax Financial News', 'https://www.infomax.co.kr'),
('Bond Reports', 'bond', 'Securities Firm Bond Analysis Reports', 'https://finance.naver.com');

-- MPB Minutes table
CREATE TABLE mpb_minutes (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    date DATE NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    discussion TEXT,
    decision TEXT,
    link TEXT,
    pdf_path TEXT,
    source_id INTEGER REFERENCES data_sources(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- News articles table
CREATE TABLE news_articles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    date DATE NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    link TEXT,
    source_id INTEGER REFERENCES data_sources(id),
    author VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bond reports table
CREATE TABLE bond_reports (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    date DATE NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    link TEXT,
    source_id INTEGER REFERENCES data_sources(id),
    securities_firm VARCHAR(255),
    report_type VARCHAR(100),
    pdf_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Call rates table
CREATE TABLE call_rates (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    call_rate DECIMAL(5,4) NOT NULL,
    change_from_previous DECIMAL(5,4),
    announcement_date DATE,
    effective_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Processed texts table (for storing tokenized and cleaned text)
CREATE TABLE processed_texts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    source_table VARCHAR(50) NOT NULL, -- 'mpb_minutes', 'news_articles', 'bond_reports'
    source_id UUID NOT NULL,
    original_text TEXT,
    cleaned_text TEXT,
    tokens_pos JSONB, -- Store tokenized text with POS tags as JSON
    processing_version VARCHAR(20) DEFAULT '1.0',
    label INTEGER, -- 0: rate decrease, 1: rate increase, NULL: no change/unknown
    label_date DATE, -- Date when the label was determined
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- N-gram analysis table
CREATE TABLE ngram_analysis (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    processed_text_id UUID REFERENCES processed_texts(id),
    ngram_size INTEGER NOT NULL CHECK (ngram_size BETWEEN 1 AND 5),
    ngrams JSONB NOT NULL, -- Store n-grams as JSON array
    frequency_data JSONB, -- Store frequency analysis results
    sentiment_score DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model results table
CREATE TABLE model_results (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    processed_text_id UUID REFERENCES processed_texts(id),
    prediction INTEGER, -- 0: decrease, 1: increase
    confidence_score DECIMAL(5,4),
    feature_importance JSONB,
    training_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Predictions table (for final predictions)
CREATE TABLE predictions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    prediction_date DATE NOT NULL,
    target_date DATE NOT NULL, -- Date for which the prediction is made (usually 2 months later)
    predicted_direction INTEGER NOT NULL, -- 0: decrease, 1: increase
    confidence_score DECIMAL(5,4),
    actual_direction INTEGER, -- Actual outcome (filled later)
    actual_rate_change DECIMAL(5,4),
    model_ensemble JSONB, -- Store multiple model results
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance

-- Primary search indexes
CREATE INDEX idx_mpb_minutes_date ON mpb_minutes(date);
CREATE INDEX idx_news_articles_date ON news_articles(date);
CREATE INDEX idx_bond_reports_date ON bond_reports(date);
CREATE INDEX idx_call_rates_date ON call_rates(date);
CREATE INDEX idx_processed_texts_source ON processed_texts(source_table, source_id);
CREATE INDEX idx_processed_texts_label ON processed_texts(label) WHERE label IS NOT NULL;

-- Full-text search indexes for Korean text
CREATE INDEX idx_mpb_minutes_content_gin ON mpb_minutes USING GIN (to_tsvector('korean', COALESCE(content, '')));
CREATE INDEX idx_mpb_minutes_discussion_gin ON mpb_minutes USING GIN (to_tsvector('korean', COALESCE(discussion, '')));
CREATE INDEX idx_news_articles_content_gin ON news_articles USING GIN (to_tsvector('korean', COALESCE(content, '')));
CREATE INDEX idx_bond_reports_content_gin ON bond_reports USING GIN (to_tsvector('korean', COALESCE(content, '')));

-- JSONB indexes for n-gram analysis
CREATE INDEX idx_ngram_analysis_ngrams ON ngram_analysis USING GIN (ngrams);
CREATE INDEX idx_ngram_analysis_frequency ON ngram_analysis USING GIN (frequency_data);
CREATE INDEX idx_model_results_features ON model_results USING GIN (feature_importance);

-- Trigram indexes for fuzzy text search
CREATE INDEX idx_mpb_minutes_title_trigram ON mpb_minutes USING GIN (title gin_trgm_ops);
CREATE INDEX idx_news_articles_title_trigram ON news_articles USING GIN (title gin_trgm_ops);
CREATE INDEX idx_bond_reports_title_trigram ON bond_reports USING GIN (title gin_trgm_ops);

-- Composite indexes for common queries
CREATE INDEX idx_processed_texts_date_label ON processed_texts(label_date, label) WHERE label IS NOT NULL;
CREATE INDEX idx_predictions_target_confidence ON predictions(target_date, confidence_score);

-- Partitioning for large tables (optional, can be implemented later)
-- CREATE TABLE news_articles_2024 PARTITION OF news_articles FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- Functions for common operations

-- Function to get text similarity using trigrams
CREATE OR REPLACE FUNCTION text_similarity(text1 TEXT, text2 TEXT)
RETURNS FLOAT AS $$
BEGIN
    RETURN similarity(text1, text2);
END;
$$ LANGUAGE plpgsql;

-- Function to calculate rate change prediction accuracy
CREATE OR REPLACE FUNCTION calculate_prediction_accuracy(start_date DATE, end_date DATE)
RETURNS TABLE(total_predictions INTEGER, correct_predictions INTEGER, accuracy DECIMAL) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_predictions,
        COUNT(CASE WHEN predicted_direction = actual_direction THEN 1 END)::INTEGER as correct_predictions,
        ROUND(
            COUNT(CASE WHEN predicted_direction = actual_direction THEN 1 END)::DECIMAL / 
            NULLIF(COUNT(*), 0) * 100, 2
        ) as accuracy
    FROM predictions 
    WHERE prediction_date BETWEEN start_date AND end_date 
    AND actual_direction IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Views for common queries

-- View for latest call rates
CREATE VIEW latest_call_rates AS
SELECT 
    date,
    call_rate,
    change_from_previous,
    LAG(call_rate) OVER (ORDER BY date) as previous_rate
FROM call_rates 
ORDER BY date DESC;

-- View for labeled training data
CREATE VIEW training_data AS
SELECT 
    pt.id,
    pt.source_table,
    pt.cleaned_text,
    pt.tokens_pos,
    pt.label,
    pt.label_date,
    CASE 
        WHEN pt.source_table = 'mpb_minutes' THEN mm.title
        WHEN pt.source_table = 'news_articles' THEN na.title
        WHEN pt.source_table = 'bond_reports' THEN br.title
    END as title,
    CASE 
        WHEN pt.source_table = 'mpb_minutes' THEN mm.date
        WHEN pt.source_table = 'news_articles' THEN na.date
        WHEN pt.source_table = 'bond_reports' THEN br.date
    END as source_date
FROM processed_texts pt
LEFT JOIN mpb_minutes mm ON pt.source_table = 'mpb_minutes' AND pt.source_id = mm.id
LEFT JOIN news_articles na ON pt.source_table = 'news_articles' AND pt.source_id = na.id
LEFT JOIN bond_reports br ON pt.source_table = 'bond_reports' AND pt.source_id = br.id
WHERE pt.label IS NOT NULL;

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mpb_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mpb_user;

-- Comments for documentation
COMMENT ON TABLE mpb_minutes IS 'Monetary Policy Board meeting minutes from Bank of Korea';
COMMENT ON TABLE news_articles IS 'Financial news articles from various sources';
COMMENT ON TABLE bond_reports IS 'Bond analysis reports from securities firms';
COMMENT ON TABLE call_rates IS 'Historical call rate data from Bank of Korea';
COMMENT ON TABLE processed_texts IS 'Processed and tokenized text data for ML analysis';
COMMENT ON TABLE ngram_analysis IS 'N-gram analysis results for sentiment analysis';
COMMENT ON TABLE model_results IS 'Machine learning model prediction results';
COMMENT ON TABLE predictions IS 'Final ensemble predictions for interest rate changes';

COMMENT ON COLUMN processed_texts.tokens_pos IS 'JSON array of [token, POS_tag] pairs from Korean NLP processing';
COMMENT ON COLUMN processed_texts.label IS '0=rate decrease, 1=rate increase, NULL=no significant change';
COMMENT ON COLUMN ngram_analysis.ngrams IS 'JSON array of n-gram sequences extracted from text';
COMMENT ON COLUMN model_results.feature_importance IS 'JSON object containing feature importance scores from ML models';