#!/usr/bin/env python3
"""
sentence_nbc_model.py
문장 단위 NBC 모델 학습 (논문 방법론 구현)
- 4백만 문장 학습
- 30회 배깅으로 안정적 점수 획득
- 현실적 F1 점수 달성
"""

import numpy as np
import pandas as pd
import pickle
import json
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.feature_extraction import DictVectorizer
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import joblib
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent

class SentenceNBC:
    """문장 단위 Naive Bayes Classifier with Bagging"""

    def __init__(self, n_estimators=30, test_size=0.1, random_state=33):
        self.n_estimators = n_estimators  # 배깅 횟수 (논문: 30)
        self.test_size = test_size  # 테스트 비율 (논문: 10%)
        self.random_state = random_state
        self.models = []
        self.vectorizers = []
        self.ngram_scores = defaultdict(list)  # 각 n-gram의 30회 점수

    def load_data(self):
        """문장 n-gram 데이터 로드"""
        print("\nLoading sentence n-gram data...")

        # 문장-ngram 데이터 로드
        ngram_path = PROJECT_ROOT / "preprocess/sentence_ngram/sentence_ngrams.pkl"

        if not ngram_path.exists():
            raise FileNotFoundError(
                "sentence_ngrams.pkl not found! Run sentence_ngram_extractor.py first"
            )

        with open(ngram_path, 'rb') as f:
            sentence_ngrams = pickle.load(f)

        print(f"  Loaded {len(sentence_ngrams):,} sentences with n-grams")

        # 라벨 분포 확인
        labels = [item['label'] for item in sentence_ngrams]
        print(f"  Dovish (0): {labels.count(0):,}")
        print(f"  Hawkish (1): {labels.count(1):,}")

        return sentence_ngrams

    def prepare_features(self, sentence_ngrams):
        """n-gram을 특징 벡터로 변환"""
        print("\nPreparing feature vectors...")

        # n-gram을 dictionary 형식으로 변환
        features = []
        labels = []

        for item in tqdm(sentence_ngrams, desc="Converting to features"):
            # n-gram 빈도를 dictionary로
            ngram_dict = {}
            for ngram in item['ngrams']:
                ngram_dict[ngram] = ngram_dict.get(ngram, 0) + 1

            features.append(ngram_dict)
            labels.append(item['label'])

        return features, np.array(labels)

    def train_with_bagging(self, features, labels):
        """30회 배깅으로 모델 학습"""
        print(f"\nTraining with {self.n_estimators}x bagging...")

        all_scores = []

        for i in tqdm(range(self.n_estimators), desc="Bagging iterations"):
            # Train/Test 분할 (매번 다른 랜덤 시드)
            X_train_dict, X_test_dict, y_train, y_test = train_test_split(
                features, labels,
                test_size=self.test_size,
                random_state=self.random_state + i,
                stratify=labels
            )

            # DictVectorizer로 변환
            vectorizer = DictVectorizer()
            X_train = vectorizer.fit_transform(X_train_dict)
            X_test = vectorizer.transform(X_test_dict)

            # Naive Bayes 학습
            model = MultinomialNB(alpha=1.0)  # Laplace smoothing
            model.fit(X_train, y_train)

            # 예측 및 평가
            y_pred = model.predict(X_test)
            f1 = f1_score(y_test, y_pred)

            # 저장
            self.models.append(model)
            self.vectorizers.append(vectorizer)
            all_scores.append(f1)

            # 각 n-gram의 조건부 확률 저장 (극성 점수 계산용)
            feature_names = vectorizer.get_feature_names_out()
            log_prob_0 = model.feature_log_prob_[0]  # Dovish
            log_prob_1 = model.feature_log_prob_[1]  # Hawkish

            for idx, ngram in enumerate(feature_names):
                # Hawkish 확률 - Dovish 확률 = 극성 점수
                polarity_score = log_prob_1[idx] - log_prob_0[idx]
                self.ngram_scores[ngram].append(polarity_score)

            if (i + 1) % 5 == 0:
                print(f"    Iteration {i+1}: F1={f1:.4f}, Avg F1={np.mean(all_scores):.4f}")

        return all_scores

    def calculate_ngram_polarity(self):
        """30회 배깅 결과로 n-gram 극성 결정"""
        print(f"\nCalculating n-gram polarity from {self.n_estimators} iterations...")

        ngram_polarity = {}
        hawkish_ngrams = []
        dovish_ngrams = []

        for ngram, scores in self.ngram_scores.items():
            # 30회 점수의 평균
            avg_score = np.mean(scores)
            std_score = np.std(scores)

            ngram_polarity[ngram] = {
                'mean_score': avg_score,
                'std_score': std_score,
                'num_iterations': len(scores)
            }

            # 극성 분류 (양수면 Hawkish, 음수면 Dovish)
            if avg_score > 0:
                hawkish_ngrams.append(ngram)
            else:
                dovish_ngrams.append(ngram)

        print(f"  Hawkish n-grams: {len(hawkish_ngrams):,}")
        print(f"  Dovish n-grams: {len(dovish_ngrams):,}")

        return ngram_polarity, hawkish_ngrams, dovish_ngrams

    def evaluate_ensemble(self, features, labels):
        """앙상블 모델 평가"""
        print("\nEvaluating ensemble model...")

        # 전체 데이터를 한 번 더 분할 (최종 평가용)
        X_train_dict, X_test_dict, y_train, y_test = train_test_split(
            features, labels,
            test_size=self.test_size,
            random_state=self.random_state + 100,
            stratify=labels
        )

        # 앙상블 예측 (다수결 투표)
        all_predictions = []
        all_probabilities = []  # 확률 저장 추가

        for model, vectorizer in zip(self.models, self.vectorizers):
            X_test = vectorizer.transform(X_test_dict)
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)  # 확률 예측
            all_predictions.append(y_pred)
            all_probabilities.append(y_proba[:, 1])  # Hawkish 확률

        # 다수결 투표
        ensemble_pred = np.array(all_predictions).mean(axis=0)
        ensemble_proba = np.array(all_probabilities).mean(axis=0)  # 평균 확률
        ensemble_pred = (ensemble_pred >= 0.5).astype(int)

        # 확률 저장 (PR 곡선용)
        self.test_labels = y_test
        self.test_proba = ensemble_proba

        # 성능 메트릭
        accuracy = accuracy_score(y_test, ensemble_pred)
        precision = precision_score(y_test, ensemble_pred)
        recall = recall_score(y_test, ensemble_pred)
        f1 = f1_score(y_test, ensemble_pred)

        print(f"\nEnsemble Performance:")
        print(f"  Accuracy:  {accuracy:.4f}")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall:    {recall:.4f}")
        print(f"  F1-Score:  {f1:.4f}")

        # Classification Report
        print("\nClassification Report:")
        print(classification_report(y_test, ensemble_pred,
                                   target_names=['Dovish', 'Hawkish']))

        # Confusion Matrix
        cm = confusion_matrix(y_test, ensemble_pred)

        return accuracy, precision, recall, f1, cm

    def plot_results(self, cm, f1_scores, output_dir):
        """결과 시각화"""
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        # 1. Confusion Matrix
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=['Dovish', 'Hawkish'],
                    yticklabels=['Dovish', 'Hawkish'],
                    ax=axes[0])
        axes[0].set_title('Confusion Matrix (Ensemble)')
        axes[0].set_xlabel('Predicted')
        axes[0].set_ylabel('Actual')

        # 2. F1 Score Distribution (30 iterations)
        axes[1].hist(f1_scores, bins=15, edgecolor='black', alpha=0.7)
        axes[1].axvline(np.mean(f1_scores), color='red',
                       linestyle='dashed', linewidth=2,
                       label=f'Mean: {np.mean(f1_scores):.3f}')
        axes[1].set_xlabel('F1 Score')
        axes[1].set_ylabel('Frequency')
        axes[1].set_title(f'F1 Distribution ({len(f1_scores)} iterations)')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        # 3. Performance by Iteration
        axes[2].plot(range(1, len(f1_scores)+1), f1_scores, 'o-', alpha=0.7)
        axes[2].axhline(np.mean(f1_scores), color='red',
                       linestyle='dashed', alpha=0.5,
                       label=f'Mean: {np.mean(f1_scores):.3f}')
        axes[2].set_xlabel('Iteration')
        axes[2].set_ylabel('F1 Score')
        axes[2].set_title('Bagging Performance')
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)

        plt.tight_layout()
        output_path = output_dir / "sentence_nbc_results.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"\n✓ Saved {output_path}")
        plt.close()

def main():
    """메인 실행 함수"""
    print("="*60)
    print("Sentence-Level NBC with 30x Bagging")
    print("="*60)

    # 출력 디렉토리 생성
    output_dir = PROJECT_ROOT / "modeling/sentence_nbc"
    output_dir.mkdir(exist_ok=True, parents=True)

    # 모델 초기화
    nbc = SentenceNBC(n_estimators=30, test_size=0.1)

    # 1. 데이터 로드
    sentence_ngrams = nbc.load_data()

    # 2. 특징 벡터 준비
    features, labels = nbc.prepare_features(sentence_ngrams)

    # 3. 30회 배깅으로 학습
    f1_scores = nbc.train_with_bagging(features, labels)

    # 4. n-gram 극성 계산
    ngram_polarity, hawkish_ngrams, dovish_ngrams = nbc.calculate_ngram_polarity()

    # 5. 앙상블 평가
    accuracy, precision, recall, f1, cm = nbc.evaluate_ensemble(features, labels)

    # 6. 결과 시각화
    nbc.plot_results(cm, f1_scores, output_dir)

    # 7. 결과 저장
    # 모델 저장
    model_data = {
        'models': nbc.models,
        'vectorizers': nbc.vectorizers,
        'ngram_scores': dict(nbc.ngram_scores)
    }
    joblib.dump(model_data, output_dir / "sentence_nbc_ensemble.pkl")
    print(f"✓ Saved sentence_nbc_ensemble.pkl")

    # n-gram 극성 저장
    polarity_df = pd.DataFrame(ngram_polarity).T
    polarity_df.to_csv(output_dir / "ngram_polarity.csv")
    print(f"✓ Saved ngram_polarity.csv")

    # Hawkish/Dovish n-gram 리스트 저장
    with open(output_dir / "hawkish_ngrams.txt", 'w', encoding='utf-8') as f:
        for ngram in sorted(hawkish_ngrams)[:100]:  # Top 100
            f.write(f"{ngram}\n")
    print(f"✓ Saved hawkish_ngrams.txt")

    with open(output_dir / "dovish_ngrams.txt", 'w', encoding='utf-8') as f:
        for ngram in sorted(dovish_ngrams)[:100]:  # Top 100
            f.write(f"{ngram}\n")
    print(f"✓ Saved dovish_ngrams.txt")

    # 통계 정보 저장
    stats = {
        'total_sentences': len(sentence_ngrams),
        'n_estimators': nbc.n_estimators,
        'test_size': nbc.test_size,
        'mean_f1': float(np.mean(f1_scores)),
        'std_f1': float(np.std(f1_scores)),
        'ensemble_accuracy': float(accuracy),
        'ensemble_precision': float(precision),
        'ensemble_recall': float(recall),
        'ensemble_f1': float(f1),
        'hawkish_ngrams': len(hawkish_ngrams),
        'dovish_ngrams': len(dovish_ngrams),
        'confusion_matrix': cm.tolist()  # 혼동행렬 추가
    }

    with open(output_dir / "model_stats.json", 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✓ Saved model_stats.json")

    # PR 곡선용 데이터 저장
    if hasattr(nbc, 'test_labels') and hasattr(nbc, 'test_proba'):
        pr_data = {
            'true_labels': nbc.test_labels.tolist(),
            'predicted_proba': nbc.test_proba.tolist()
        }
        with open(output_dir / "pr_curve_data.json", 'w') as f:
            json.dump(pr_data, f)
        print(f"✓ Saved pr_curve_data.json")

    print("\n" + "="*60)
    print("✅ Sentence NBC training complete!")
    print(f"   Mean F1: {np.mean(f1_scores):.3f} ± {np.std(f1_scores):.3f}")
    print(f"   Ensemble F1: {f1:.3f}")
    print("="*60)

    return nbc, stats

if __name__ == "__main__":
    nbc, stats = main()