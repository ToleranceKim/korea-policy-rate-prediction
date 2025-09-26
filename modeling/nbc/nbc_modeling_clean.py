#!/usr/bin/env python3
"""
NBC 모델 학습 (Data Leakage 제거 버전)
- Train 데이터만으로 vocabulary 생성
- Test는 Train vocabulary만 사용
- 직접 구현 Naive Bayes
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent

def load_data():
    """날짜별 n-gram과 라벨 로드"""
    print("="*60)
    print("NBC Model Training (No Data Leakage)")
    print("="*60)

    print("\nLoading data...")

    # date_ngram_real.json 로드
    with open(PROJECT_ROOT / "modeling/nbc/date_ngram_real.json", 'r', encoding='utf-8') as f:
        date_ngram = json.load(f)

    # date_label_real.json 로드
    with open(PROJECT_ROOT / "modeling/nbc/date_label_real.json", 'r', encoding='utf-8') as f:
        date_label = json.load(f)

    # DataFrame 생성
    data = [{"date": date, "ngrams": ngrams, "label": date_label[date]}
            for date, ngrams in date_ngram.items()]
    df = pd.DataFrame(data)
    df.set_index('date', inplace=True)

    print(f"Loaded {len(df)} dates")
    print(f"  Dovish: {(df['label'] == 0).sum()}")
    print(f"  Hawkish: {(df['label'] == 1).sum()}")

    return df

def split_data(df):
    """Train/Test 분할"""
    print("\nSplitting data...")
    df_train, df_test = train_test_split(df, test_size=0.1, random_state=33, stratify=df['label'])
    print(f"  Train: {len(df_train)} dates")
    print(f"  Test: {len(df_test)} dates")
    return df_train, df_test

def build_vocabulary(df_train, min_freq=5):
    """Train 데이터만으로 vocabulary 생성"""
    print("\nBuilding vocabulary from train data only...")

    count_0 = {}  # Dovish n-gram 빈도
    count_1 = {}  # Hawkish n-gram 빈도

    # Train 데이터에서 빈도 계산
    for _, row in df_train.iterrows():
        for ngram in row['ngrams']:
            if row['label'] == 0:
                count_0[ngram] = count_0.get(ngram, 0) + 1
            else:
                count_1[ngram] = count_1.get(ngram, 0) + 1

    print(f"  Unique n-grams in Dovish: {len(count_0):,}")
    print(f"  Unique n-grams in Hawkish: {len(count_1):,}")

    # Vocabulary DataFrame 생성
    unique_ngram = list(set(list(count_0.keys()) + list(count_1.keys())))
    vocab_df = pd.DataFrame(index=unique_ngram)

    vocab_df['count_0'] = pd.Series(count_0)
    vocab_df['count_1'] = pd.Series(count_1)
    vocab_df = vocab_df.fillna(0)

    # 총 빈도 계산
    vocab_df['sum'] = vocab_df['count_0'] + vocab_df['count_1']

    # 최소 빈도 이상만 선택
    vocab_df = vocab_df[vocab_df['sum'] >= min_freq]
    print(f"  Vocabulary size (freq >= {min_freq}): {len(vocab_df):,}")

    # 확률 계산
    sum_0 = vocab_df['count_0'].sum()
    sum_1 = vocab_df['count_1'].sum()
    sum_tot = sum_0 + sum_1

    # Smoothing 없이 (기존 노트북과 동일)
    vocab_df['prob_0'] = vocab_df['count_0'] / sum_0
    vocab_df['prob_1'] = vocab_df['count_1'] / sum_1

    # Epsilon 추가로 log(0) 방지 (warning 제거용)
    epsilon = 1e-100  # 극소값
    vocab_df['prob_0'] = vocab_df['prob_0'].replace(0, epsilon)
    vocab_df['prob_1'] = vocab_df['prob_1'].replace(0, epsilon)

    print(f"  Total n-grams: {int(sum_tot):,}")
    print(f"    Dovish: {int(sum_0):,} ({sum_0/sum_tot*100:.1f}%)")
    print(f"    Hawkish: {int(sum_1):,} ({sum_1/sum_tot*100:.1f}%)")

    return vocab_df, sum_0/sum_tot, sum_1/sum_tot

def predict(ngrams, vocab_df, prior_0, prior_1):
    """Naive Bayes 예측"""
    # Prior 확률 (log)
    log_prob_0 = np.log(prior_0)
    log_prob_1 = np.log(prior_1)

    # Likelihood 계산
    for ngram in ngrams:
        if ngram in vocab_df.index:  # Train vocabulary에 있는 경우만
            log_prob_0 += np.log(vocab_df.at[ngram, 'prob_0'])
            log_prob_1 += np.log(vocab_df.at[ngram, 'prob_1'])
        # Unknown n-gram은 무시 (기존 노트북과 동일)

    return 1 if log_prob_1 > log_prob_0 else 0

def evaluate_model(df_test, vocab_df, prior_0, prior_1):
    """모델 평가"""
    print("\nEvaluating model...")

    # 예측
    df_test['y_pred'] = df_test['ngrams'].apply(
        lambda x: predict(x, vocab_df, prior_0, prior_1)
    )

    y_true = df_test['label'].values
    y_pred = df_test['y_pred'].values

    # 성능 메트릭
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)

    print("\n" + "="*60)
    print("Model Performance (No Data Leakage)")
    print("="*60)

    print(f"\nMetrics:")
    print(f"  Accuracy:  {accuracy:.4f}")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  F1-Score:  {f1:.4f}")

    # Classification Report
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred,
                              target_names=['Dovish (0)', 'Hawkish (1)']))

    # Confusion Matrix
    cm = confusion_matrix(y_true, y_pred)
    print("Confusion Matrix:")
    print(f"  TP (True Hawkish):  {cm[1, 1]}")
    print(f"  FP (False Hawkish): {cm[0, 1]}")
    print(f"  TN (True Dovish):   {cm[0, 0]}")
    print(f"  FN (False Dovish):  {cm[1, 0]}")

    # 시각화
    plot_results(cm, y_true, y_pred, df_test.index)

    return accuracy, precision, recall, f1

def plot_results(cm, y_true, y_pred, dates):
    """결과 시각화"""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    # Confusion Matrix
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Predicted 0', 'Predicted 1'],
                yticklabels=['True 0', 'True 1'],
                ax=axes[0])
    axes[0].set_xlabel('Predicted')
    axes[0].set_ylabel('True')
    axes[0].set_title('Confusion Matrix (No Data Leakage)')

    # Prediction vs Truth
    axes[1].plot(range(len(y_true)), y_true, 'o-', label='True', alpha=0.7)
    axes[1].plot(range(len(y_pred)), y_pred, 'x--', label='Predicted', alpha=0.7)
    axes[1].set_xlabel('Test Sample Index')
    axes[1].set_ylabel('Label (0=Dovish, 1=Hawkish)')
    axes[1].set_title('Predictions vs Truth')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    output_path = PROJECT_ROOT / "modeling/nbc/confusion_matrix_clean.png"
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    print(f"\n✓ Saved {output_path}")
    plt.close()

def main():
    """메인 실행"""
    # 1. 데이터 로드
    df = load_data()

    # 2. Train/Test 분할
    df_train, df_test = split_data(df)

    # 3. Train 데이터만으로 vocabulary 생성
    vocab_df, prior_0, prior_1 = build_vocabulary(df_train, min_freq=5)

    # 4. 모델 평가
    accuracy, precision, recall, f1 = evaluate_model(df_test, vocab_df, prior_0, prior_1)

    # 5. 결과 저장
    results = {
        'train_size': len(df_train),
        'test_size': len(df_test),
        'vocabulary_size': len(vocab_df),
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'prior_dovish': float(prior_0),
        'prior_hawkish': float(prior_1)
    }

    with open(PROJECT_ROOT / "modeling/nbc/model_results_clean.json", 'w') as f:
        json.dump(results, f, indent=2)
    print("\n✓ Saved model_results_clean.json")

    print("\n" + "="*60)
    print(f"✅ NBC modeling completed! (Clean F1-Score: {f1:.3f})")
    print("="*60)

if __name__ == "__main__":
    main()