import csv
from collections import Counter

def count_ngrams_in_file(file_path, chunk_size=100000):
    ngram_counter = Counter()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        chunk = []
        for line in file:
            ngram = line.strip()
            chunk.append(ngram)
            
            if len(chunk) >= chunk_size:
                ngram_counter.update(chunk)
                chunk = []
        # 마지막 남은 chunk 처리
        if chunk:
            ngram_counter.update(chunk)
    
    return ngram_counter

def filter_and_save_ngrams(ngram_counter, output_file_path, min_frequency=5):
    with open(output_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ngram', 'frequency'])  # CSV 헤더 작성
        
        for ngram, count in ngram_counter.items():
            if count > min_frequency:
                writer.writerow([ngram, count])

def main():
    input_file_path = '../../preprocess/ngram/ngram_results.csv'
    output_file_path = 'filtered_ngrams.csv'
    
    # n-gram 빈도수 계산
    ngram_counter = count_ngrams_in_file(input_file_path)
    
    # 빈도수가 5 이하인 항목 제거 후 CSV로 저장
    filter_and_save_ngrams(ngram_counter, output_file_path)

if __name__ == '__main__':
    main()