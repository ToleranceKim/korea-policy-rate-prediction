import ast

class NGram:
    def __init__(self):
        pass


    # 
    def str_to_list(self, tokens_str):
        return ast.literal_eval(tokens_str)
    
    # remove_pos: remove tokens with specific POS tags that are not needed
    def remove_pos(self, tokens, pos_tags=['NNG', 'VA', 'MAG', 'VV', 'VCN']):
        return [token for token, pos in tokens if pos in pos_tags]

    # ngramize: generate n-grams from tokens
    def ngramize(self, filtered_tokens, n):
        ngrams = []
        for i in range(len(filtered_tokens) - n + 1):
            ngram = ' '.join(filtered_tokens[i:i + n])  # 띄어쓰기로 연결된 문자열 생성
            ngrams.append(ngram)
        return ngrams