#!/bin/bash

# 문장 단위 NBC 파이프라인 실행 스크립트
# 논문 방법론에 따라 4백만 문장 학습

echo "============================================================"
echo "Sentence-Level NBC Pipeline (Paper Method)"
echo "============================================================"
echo ""

# 1. 문장 분리 (122K 문서 → 4M+ 문장)
echo "Step 1: Splitting documents into sentences..."
echo "----------------------------------------"
python preprocess/sentence_split/sentence_splitter.py
if [ $? -ne 0 ]; then
    echo "❌ Error in sentence splitting. Exiting."
    exit 1
fi
echo ""

# 2. 문장별 n-gram 추출
echo "Step 2: Extracting n-grams from sentences..."
echo "----------------------------------------"
python preprocess/sentence_ngram/sentence_ngram_extractor.py
if [ $? -ne 0 ]; then
    echo "❌ Error in n-gram extraction. Exiting."
    exit 1
fi
echo ""

# 3. NBC 모델 학습 (30x 배깅)
echo "Step 3: Training NBC with 30x bagging..."
echo "----------------------------------------"
python modeling/sentence_nbc/sentence_nbc_model.py
if [ $? -ne 0 ]; then
    echo "❌ Error in NBC training. Exiting."
    exit 1
fi
echo ""

echo "============================================================"
echo "✅ Sentence-level NBC pipeline completed successfully!"
echo "============================================================"
echo ""
echo "Results saved in:"
echo "  - preprocess/sentence_split/sentence_corpus.csv"
echo "  - preprocess/sentence_ngram/sentence_ngrams.pkl"
echo "  - modeling/sentence_nbc/sentence_nbc_ensemble.pkl"
echo "  - modeling/sentence_nbc/model_stats.json"