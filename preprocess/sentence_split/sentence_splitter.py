#!/usr/bin/env python3
"""
sentence_splitter.py
문서를 문장 단위로 분리하여 논문과 동일한 sentence-level 학습 데이터 생성
논문: "We randomly divide our labeled sentences (more than 4 million sentences)"
"""

import pandas as pd
import re
from pathlib import Path
from tqdm import tqdm
import json

PROJECT_ROOT = Path(__file__).parent.parent.parent

class KoreanSentenceSplitter:
    """한국어 문장 분리기"""

    def __init__(self):
        # 문장 종결 패턴
        self.sentence_endings = re.compile(
            r'[.!?]\s*(?=[가-힣A-Z])|'  # 마침표, 느낌표, 물음표 + 다음 문장 시작
            r'(?<=[다라마바사아자차카타파하])\.\s*(?=[가-힣A-Z])|'  # 한국어 종결 + 마침표
            r'(?<=[요죠])\.\s*(?=[가-힣A-Z])|'  # 존댓말 종결 + 마침표
            r'(?<=[음임])\.\s*(?=[가-힣A-Z])'  # 명사형 종결 + 마침표
        )

        # 분리하지 말아야 할 패턴 (약어, 숫자 등)
        self.no_split_patterns = [
            r'\d+\.\d+',  # 소수점
            r'[A-Z]\.[A-Z]',  # 약어 (U.S.)
            r'\d+\.\s*\d+',  # 번호 매기기 (1. 2. 3.)
        ]

    def split_sentences(self, text):
        """텍스트를 문장 단위로 분리"""
        if not text or pd.isna(text):
            return []

        # 줄바꿈을 공백으로 치환
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = re.sub(r'\s+', ' ', text).strip()

        if not text:
            return []

        # 보호 패턴 임시 치환
        protected_text = text
        replacements = []
        for pattern in self.no_split_patterns:
            matches = re.finditer(pattern, protected_text)
            for i, match in enumerate(matches):
                placeholder = f"__PROTECT_{len(replacements)}__"
                replacements.append(match.group())
                protected_text = protected_text.replace(match.group(), placeholder)

        # 문장 분리
        sentences = self.sentence_endings.split(protected_text)

        # 보호 패턴 복원
        restored_sentences = []
        for sent in sentences:
            if sent.strip():
                for i, original in enumerate(replacements):
                    sent = sent.replace(f"__PROTECT_{i}__", original)
                restored_sentences.append(sent.strip())

        # 너무 짧은 문장 필터링 (10자 미만)
        sentences = [s for s in restored_sentences if len(s) >= 10]

        return sentences if sentences else [text.strip()]

def process_corpus():
    """corpus_data.csv를 문장 단위로 분리"""
    print("="*60)
    print("Sentence-Level Data Generation")
    print("="*60)

    # 코퍼스 로드
    corpus_path = PROJECT_ROOT / "preprocess/data_combine/corpus_data.csv"
    print(f"\nLoading corpus from {corpus_path}")
    df_corpus = pd.read_csv(corpus_path)

    # NaN PK 제거
    df_corpus = df_corpus.dropna(subset=['pk'])
    print(f"Loaded {len(df_corpus):,} documents (NaN removed)")

    # 통계
    print(f"\nCorpus statistics:")
    print(f"  Dovish: {(df_corpus['Label']==0).sum():,} documents")
    print(f"  Hawkish: {(df_corpus['Label']==1).sum():,} documents")

    # 문장 분리
    splitter = KoreanSentenceSplitter()
    sentence_data = []

    print(f"\nSplitting documents into sentences...")
    for _, row in tqdm(df_corpus.iterrows(), total=len(df_corpus), desc="Processing"):
        text = row['Content']
        if pd.isna(text):
            continue

        sentences = splitter.split_sentences(text)

        for sent in sentences:
            sentence_data.append({
                'pk': row['pk'],
                'date': row['Date'],
                'label': int(row['Label']),
                'sentence': sent
            })

    # DataFrame 생성
    df_sentences = pd.DataFrame(sentence_data)

    print(f"\nSentence-level statistics:")
    print(f"  Total sentences: {len(df_sentences):,}")
    print(f"  Avg sentences per doc: {len(df_sentences)/len(df_corpus):.1f}")
    print(f"  Dovish sentences: {(df_sentences['label']==0).sum():,} ({(df_sentences['label']==0).sum()/len(df_sentences)*100:.1f}%)")
    print(f"  Hawkish sentences: {(df_sentences['label']==1).sum():,} ({(df_sentences['label']==1).sum()/len(df_sentences)*100:.1f}%)")

    # 저장
    output_dir = PROJECT_ROOT / "preprocess/sentence_split"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "sentence_corpus.csv"
    df_sentences.to_csv(output_path, index=False)
    print(f"\n✓ Saved {output_path}")

    # 통계 저장
    stats = {
        'total_documents': len(df_corpus),
        'total_sentences': len(df_sentences),
        'avg_sentences_per_doc': len(df_sentences) / len(df_corpus),
        'dovish_sentences': int((df_sentences['label']==0).sum()),
        'hawkish_sentences': int((df_sentences['label']==1).sum()),
        'unique_dates': df_sentences['date'].nunique()
    }

    with open(output_dir / "sentence_stats.json", 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✓ Saved sentence_stats.json")

    return df_sentences

if __name__ == "__main__":
    df_sentences = process_corpus()
    print(f"\n✅ Generated {len(df_sentences):,} sentences for NBC training")
    print("="*60)