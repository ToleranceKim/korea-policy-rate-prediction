
import pandas as pd
import re
import string

df = pd.read_csv("/Users/belllaw/Desktop/workspace/project_1/bond/crawling/my_csv.csv")
df = df.drop(columns='Unnamed: 0')

def clean_text(text):
    # HTML 태그 제거
    text = re.sub('<.*?>', '', text)  # '<[^>]*>'

    # E-mail제거
    text = re.sub('([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', '', text)
                
    # 한글 자음, 모음 제거
    text = re.sub('([ㄱ-ㅎㅏ-ㅣ]+)', '', text)

    # 특수문자 제거
    text = re.sub('[^a-zA-Z0-9ㄱ-ㅣ가-힣]', ' ', text)

    # 공백 제거
    text = re.sub('\s+', ' ', text)

    # text = re.sub('['+string.punctuation+']', ' ', text)  # 구두점 제거
    text = re.sub('\d+\.\d+', '', text)  # 소수점 숫자 제거
    text = re.sub('\d+', '', text)  # 숫자 제거
    return text


df['Title'] = df['Title'].apply(clean_text)
df['Content'] = df['Content'].apply(clean_text)
df_cleaned = df[['Date', 'Title', 'Content', 'Link']]
df_cleaned