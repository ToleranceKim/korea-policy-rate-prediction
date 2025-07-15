# Cleansing
- TITLE과 CONTENTS의 데이터만 클렌징
- 뉴스 데이터에서 중복된 기사 제거
- 각 데이터 셋마다 정규표현식을 활용하여 데이터 클렌징
- DATE의 데이터 날짜형으로 통일

<br/>

- 날짜 컬럼의 데이터를 날짜형으로 바꾸고 정렬, 포맷 통일
```python
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df = df.sort_values(by='date')

# 포맷 통일
df['date'] = df['date'].astype(str)
df['date'] = df['date'].str.replace('-', '.')
```
<br/>


- 정규표현식 함수 만들어서 각 컬럼에 적용
```python
def cleansing_text(text):
    # 종목 코드 (괄호 안 6자리 숫자) 제거
    text = re.sub(r'\(\d{6}\)', '', text)
    
    # 특수 기호 및 광고성 텍스트 제거
    text = re.sub(r'▶ 관련기사 ◀', '', text)
    text = re.sub(r'☞[^☞]*', '', text)
    
    # 맥락과 관련 없는 리스트 및 간추린 소식 제거
    text = re.sub(r'\d+\.\s[^<]*', '', text)
    text = re.sub(r'<간추린 소식>[^-]*', '', text)
    
    # 구두점, 따옴표, 기타 특수 문자 제거
    text = re.sub(r'[▲△▶▼▽◆◇=ㆍ/·.,;:!?\'"‘’“”~∼&()→%․\[\]\-–]', '', text)
    
    # '사진', '표'와 같은 텍스트 제거
    text = re.sub(r'사진|표', '', text)
    
    # 필요한 공백 제거
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

df['title'] = df['title'].apply(cleansing_text)
df['content'] = df['content'].apply(cleansing_text)
df['discussion'] = df['discussion'].apply(cleansing_text)
df['decision'] = df['decision'].apply(cleansing_text)
```
<br/>
<br/>

### 2. 뉴스
- 중복된 기사 제거(뉴스)
```python
# 제목이 중복된 행을 찾기
duplicate_titles = df[df.duplicated(subset='제목', keep=False)]

# 중복된 제목의 인덱스를 그룹화하여 중복 관계를 표시
duplicate_groups = duplicate_titles.groupby('제목').apply(lambda x: x.index.tolist())

# 중복 제목과 관련된 인덱스 출력
print("\n중복 제목과 관련된 인덱스:")
for title, indices in duplicate_groups.items():
    print(f"제목: {title}")
    print(f"중복 인덱스: {indices}")

# TITLE과 CONTENTS 중복된 행 제거
df.drop_duplicates(subset=['제목', '내용'])
```
<br/>

