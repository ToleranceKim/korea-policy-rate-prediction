#!/usr/bin/env python3
"""
sentence_ngram_extractor.py
문장 단위 n-gram 추출 (논문 방법론 구현)
- 4백만 문장 각각에서 1-5 gram 추출
- 품사 필터링 적용
- 빈도 기반 필터링
"""

import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
import json
import pickle
from collections import defaultdict, Counter
from ekonlpy.sentiment import MPKO
from ekonlpy.tag import Mecab

PROJECT_ROOT = Path(__file__).parent.parent.parent

class SentenceNgramExtractor:
    """문장 단위 n-gram 추출기"""

    def __init__(self):
        # 형태소 분석기 초기화
        self.mpko = MPKO()
        self.mecab = Mecab()

        # POS 필터 (논문과 동일)
        self.pos_filter = {'NNG', 'VA', 'MAG', 'VV', 'VCN'}

        # n-gram 범위
        self.min_n = 1
        self.max_n = 5

        # 최소 빈도수 (논문: 15회)
        self.min_frequency = 15

    def is_english_sentence(self, sentence):
        """영어 문장 여부 판단 (간단한 휴리스틱)"""
        # ASCII 문자 비율 계산
        ascii_count = sum(1 for char in sentence if ord(char) < 128)
        total_count = len(sentence)

        if total_count == 0:
            return False

        # 70% 이상이 ASCII 문자면 영어 문장으로 간주
        return (ascii_count / total_count) > 0.7

    def tokenize_sentence(self, sentence):
        """문장 토큰화 및 POS 필터링"""
        try:
            # 영어 문장은 건너뛰기 (논문에서 한국어 텍스트 대상으로 명시)
            if self.is_english_sentence(sentence):
                return []

            # Mecab POS 태깅
            tokens_with_pos = self.mecab.pos(sentence)

            # POS 필터링
            filtered_tokens = []
            for word, pos in tokens_with_pos:
                if pos in self.pos_filter:
                    filtered_tokens.append(word)

            return filtered_tokens
        except:
            return []

    def is_valid_ngram(self, ngram):
        """중복 단어 필터링 (논문에 없지만 필수)"""
        words = ngram.split()

        # 단일 단어는 통과
        if len(words) == 1:
            return True

        # 연속 중복 제거
        for i in range(len(words)-1):
            if words[i] == words[i+1]:
                return False

        # 전체 단어의 50% 이상이 같은 단어인 경우 제거
        if len(words) > 2:
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            max_count = max(word_counts.values())
            if max_count > len(words) / 2:
                return False

        return True

    def extract_ngrams(self, tokens, n):
        """토큰 리스트에서 n-gram 추출"""
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = ' '.join(tokens[i:i+n])
            # 유효성 검사 추가
            if self.is_valid_ngram(ngram):
                ngrams.append(ngram)
        return ngrams

    def process_sentences(self, df_sentences):
        """문장별 n-gram 추출"""
        print(f"\nExtracting n-grams from {len(df_sentences):,} sentences...")

        # 문장별 n-gram 저장
        sentence_ngrams = []
        ngram_frequency = Counter()
        sentence_counter = 0  # 고유 sentence_id 카운터
        english_count = 0  # 영어 문장 카운트
        empty_token_count = 0  # 빈 토큰 카운트

        # 배치 처리
        batch_size = 10000
        num_batches = (len(df_sentences) + batch_size - 1) // batch_size

        for batch_idx in tqdm(range(num_batches), desc="Processing batches"):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(df_sentences))
            batch_df = df_sentences.iloc[start_idx:end_idx]

            for idx, row in batch_df.iterrows():
                sentence = row['sentence']

                # 영어 문장 체크
                if self.is_english_sentence(sentence):
                    english_count += 1
                    continue

                # 토큰화
                tokens = self.tokenize_sentence(sentence)
                if not tokens:
                    empty_token_count += 1
                    continue

                # 각 n에 대해 n-gram 추출
                all_ngrams = []
                for n in range(self.min_n, self.max_n + 1):
                    if len(tokens) >= n:
                        ngrams = self.extract_ngrams(tokens, n)
                        all_ngrams.extend(ngrams)

                        # 빈도수 카운팅
                        for ngram in ngrams:
                            ngram_frequency[ngram] += 1

                # 문장별 결과 저장
                if all_ngrams:
                    sentence_ngrams.append({
                        'sentence_id': sentence_counter,  # 고유 ID 사용
                        'pk': row['pk'],
                        'date': row['date'],
                        'label': row['label'],
                        'ngrams': all_ngrams,
                        'sentence': sentence
                    })
                    sentence_counter += 1

            # 중간 저장 (메모리 관리)
            if (batch_idx + 1) % 10 == 0:
                print(f"  Processed {end_idx:,} sentences, {len(ngram_frequency):,} unique n-grams")

        # 처리 통계 출력
        print(f"\nProcessing statistics:")
        print(f"  Total sentences: {len(df_sentences):,}")
        print(f"  English sentences (filtered): {english_count:,}")
        print(f"  Empty tokens (filtered): {empty_token_count:,}")
        print(f"  Valid sentences processed: {len(sentence_ngrams):,}")
        print(f"  Unique n-grams extracted: {len(ngram_frequency):,}")

        return sentence_ngrams, ngram_frequency

    def filter_by_frequency(self, sentence_ngrams, ngram_frequency):
        """빈도수 기준 필터링"""
        print(f"\nFiltering n-grams (min frequency: {self.min_frequency})...")

        # 빈도수 기준 통과한 n-gram
        valid_ngrams = {ngram for ngram, freq in ngram_frequency.items()
                        if freq >= self.min_frequency}

        print(f"  Total unique n-grams: {len(ngram_frequency):,}")
        print(f"  Valid n-grams (freq >= {self.min_frequency}): {len(valid_ngrams):,}")

        # 문장별 n-gram 필터링
        filtered_sentence_ngrams = []
        for item in tqdm(sentence_ngrams, desc="Filtering sentences"):
            filtered_ngrams = [ng for ng in item['ngrams'] if ng in valid_ngrams]

            if filtered_ngrams:  # 유효한 n-gram이 있는 경우만
                item['ngrams'] = filtered_ngrams
                filtered_sentence_ngrams.append(item)

        print(f"  Sentences with valid n-grams: {len(filtered_sentence_ngrams):,}")

        return filtered_sentence_ngrams, valid_ngrams

def main():
    """메인 실행 함수"""
    print("="*60)
    print("Sentence-Level N-gram Extraction")
    print("="*60)

    # 1. 문장 데이터 로드
    sentence_corpus_path = PROJECT_ROOT / "preprocess/sentence_split/sentence_corpus.csv"

    if not sentence_corpus_path.exists():
        print(f"❌ Error: sentence_corpus.csv not found!")
        print("Please run sentence_splitter.py first")
        return

    print(f"\nLoading sentence corpus...")
    df_sentences = pd.read_csv(sentence_corpus_path)
    print(f"  Loaded {len(df_sentences):,} sentences")

    # 2. n-gram 추출기 초기화
    extractor = SentenceNgramExtractor()

    # 3. 문장별 n-gram 추출
    sentence_ngrams, ngram_frequency = extractor.process_sentences(df_sentences)

    # 4. 빈도수 필터링
    filtered_ngrams, valid_ngrams = extractor.filter_by_frequency(
        sentence_ngrams, ngram_frequency
    )

    # 5. 결과 저장
    output_dir = PROJECT_ROOT / "preprocess/sentence_ngram"
    output_dir.mkdir(exist_ok=True)

    # 문장-ngram 매핑 저장 (pickle for efficiency)
    with open(output_dir / "sentence_ngrams.pkl", 'wb') as f:
        pickle.dump(filtered_ngrams, f)
    print(f"\n✓ Saved sentence_ngrams.pkl")

    # n-gram vocabulary 저장
    vocab_df = pd.DataFrame({
        'ngram': list(valid_ngrams),
        'frequency': [ngram_frequency[ng] for ng in valid_ngrams]
    })
    vocab_df.to_csv(output_dir / "ngram_vocabulary.csv", index=False)
    print(f"✓ Saved ngram_vocabulary.csv ({len(vocab_df):,} n-grams)")

    # 통계 정보 저장
    stats = {
        'total_sentences': len(df_sentences),
        'sentences_with_ngrams': len(filtered_ngrams),
        'total_unique_ngrams': len(ngram_frequency),
        'filtered_ngrams': len(valid_ngrams),
        'min_frequency': extractor.min_frequency,
        'ngram_range': f"{extractor.min_n}-{extractor.max_n}",
        'pos_filter': list(extractor.pos_filter)
    }

    with open(output_dir / "extraction_stats.json", 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✓ Saved extraction_stats.json")

    # 라벨별 통계
    label_stats = defaultdict(int)
    for item in filtered_ngrams:
        label_stats[item['label']] += 1

    print(f"\n" + "="*60)
    print("Extraction Results:")
    print(f"  Total sentences processed: {len(df_sentences):,}")
    print(f"  Sentences with valid n-grams: {len(filtered_ngrams):,}")
    print(f"  Unique n-grams (filtered): {len(valid_ngrams):,}")
    print(f"\nLabel distribution:")
    print(f"  Dovish (0): {label_stats[0]:,} sentences")
    print(f"  Hawkish (1): {label_stats[1]:,} sentences")
    print("="*60)

    return filtered_ngrams, valid_ngrams

if __name__ == "__main__":
    filtered_ngrams, valid_ngrams = main()
    print(f"\n✅ Sentence n-gram extraction complete!")