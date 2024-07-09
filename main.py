import pandas as pd
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords , words
import os
import syllables
import re


# Function for text extraction from URL
def ExtractFromUrl(urlid,url):
    #assigning class to extract only the article title and content
    c1='entry-title'
    c2='td-post-content tagdiv-type'
    response = requests.get(url)
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        # Extract the article title
        title_element = soup.find('h1', class_= c1)
        title = title_element.get_text() if title_element else 'Title not found'
        # Extract the article text
        text_element = soup.find('div', class_= c2)
        paragraphs = text_element.find_all('p')
        text = ' '.join([p.get_text() for p in paragraphs])
        list_items = text_element.find_all('li')
        lists=' '.join([li.get_text() for li in list_items])    
        txt1=title + text + lists
        print(txt1)
        return txt1
    else:
        print(f"Failed to fetch the webpage. Status code: {response.status_code}")
        return None

# Function to tokenize and remove stopwords from text
def processed_text(text):
    file_list = os.listdir(".\StopWords")
    # Iterate through each file
    stopwords=[]
    for file_name in file_list:
        # Check if the file is a text file (you can customize this condition as needed)
        if file_name.endswith(".txt"):
            # Create the full file path
            file_path = os.path.join("./StopWords", file_name)
            # Open and read the contents of the text file
            with open(file_path, 'r') as file:
                file_contents = file.read().strip().split('\n')
            stopwords.extend(file_contents)
    tokens = word_tokenize(text)
    filtered_tokens = [word for word in tokens if word.lower() not in stopwords and word.isalnum()]
    return filtered_tokens

# Function to count positive score in text file
def poscore(text1):
        with open(".\positive-words.txt", 'r') as file:
            positive_words = file.read().split()
        if text1==[]:
            poscore=0
            return poscore
        else:
            poscore = sum(1 for txt in text1 if txt in positive_words)
            return poscore
        
# Calculating negative score of a text file
def negscore(text1):
    with open (".\negative-words.txt",'r')as file:
        chck=file.read()
        check=chck.split()
    negiscore=0
    if text1==[]:
        return negiscore
    else:
        for txt in text1:
            if txt in check:
                negiscore-=1
            else:
                continue
        return negiscore

# main

# Text extraction from URL
df=pd.read_excel(".\Input.xlsx")
for index, row in df.iterrows():
    # Extract text from the URL
    web_text = ExtractFromUrl(row['URL_ID'],row['URL'])
    # Save the preprocessed tokens to a text file
    if web_text==None:
        #creating empty text file for url with error
        with open(row['URL_ID']+'.txt' , "w", encoding="utf-8") as file:
            file.write('')
            print("Text has been extracted from the URL and stored in",row['URL_ID'],".")
    else:
        with open(row['URL_ID']+'.txt' , "w", encoding="utf-8") as file:
            file.write(web_text)
            print("Text has been extracted from the URL and stored in",row['URL_ID'],".")

df = pd.read_excel(".\Output Data Structure.xlsx")

# Acccessing text file for analyzing
folder_path = "./"
file_names = os.listdir(folder_path)
sort = sorted(file_names)

# Iterate over text files and update DataFrame
for file_name, index in zip(sort, range(len(df))):
    if file_name.endswith('.txt'):
        file_path = os.path.join(folder_path, file_name)
        # Open and process the file
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        clean=processed_text(text)
        # Calculate positive score for the text file
        calculated_poscore = poscore(clean)
        calculated_negscore = negscore(clean)*(-1)
        # Update 'POSITIVE SCORE' column for the current row
        df.at[index, 'POSITIVE SCORE'] = calculated_poscore
        df.at[index,'NEGATIVE SCORE'] = calculated_negscore
        
        # Calculating Polarity score
        ps=(calculated_poscore - calculated_negscore)/(calculated_poscore + calculated_negscore+0.000001)
        polarity_score=round(ps,2)
        df['POLARITY SCORE'] = df['POLARITY SCORE'].astype(float)
        df.at[index,'POLARITY SCORE'] = polarity_score

        # Calculating Subjective score
        ss=(calculated_poscore + calculated_negscore)/((len(clean))+0.000001)
        subjective_score=round(ss,4)
        df['SUBJECTIVITY SCORE'] = df['SUBJECTIVITY SCORE'].astype(float)
        df.at[index,'SUBJECTIVITY SCORE'] = subjective_score

        # Calculating avg. sentence length
        total_words=len(clean)
        sentences = nltk.sent_tokenize(text)
        sentence_count = len(sentences)
        if total_words==0:
            df.at[index,'AVG SENTENCE LENGTH'] = 0
        else:
            al = total_words/sentence_count
            avg_length=round(al,2)
            df['AVG SENTENCE LENGTH'] = df['AVG SENTENCE LENGTH'].astype(float)
            df.at[index,'AVG SENTENCE LENGTH'] = avg_length

        # calculating percentage of complex words
        english_words = set(words.words())
        complex_words = []
        # Iterate through each word in the paragraph
        for word in clean:
        # Check if the word is in the NLTK words corpus and has more than two syllables
            if len(word) > 2 and word.lower() in english_words and syllables.estimate(word) > 2:
                complex_words.append(word)
        if total_words==0:
            df.at[index,'PERCENTAGE OF COMPLEX WORDS'] = 0
        else:
            pcw=len(complex_words)/len(clean)
            per_complex_words=round(pcw,3)
            df.at[index,'PERCENTAGE OF COMPLEX WORDS'] = per_complex_words

        # Calculate fog index
        if total_words==0:
            df.at[index,'FOG INDEX'] = 0
        else:
            fi=0.4*(avg_length + per_complex_words)
            fog_index=round(fi,3)
            df.at[index,'FOG INDEX'] = fog_index

        # Calculate average number of words per sentence
        if total_words==0:
            df.at[index,'AVG NUMBER OF WORDS PER SENTENCE'] = 0
        else:
            avg=len(clean)/sentence_count
            avg_no_words_per_sentence=round(avg,2)
            df.at[index,'AVG NUMBER OF WORDS PER SENTENCE'] = avg_no_words_per_sentence
            
        # Complex words count
        df.at[index,'COMPLEX WORD COUNT'] = len(complex_words)

        # Calculating word count
        df.at[index,'WORD COUNT'] = len(clean)

        # Calculating number of syllables per word
        exceptions = ["es", "ed"]
        total_syllables = 0
        for word in clean:
            if any(word.endswith(exception) for exception in exceptions):
                continue
            vowels = "aeiou"
            count = sum(1 for char in word.lower() if char in vowels)
            total_syllables += count
        df.at[index,'SYLLABLE PER WORD'] = total_syllables

        # Calculating personal pronouns using regex
        personal_pronouns = ["I", "we", "my", "ours", "us"]
        # Initialize counts
        pronoun_counts = {pronoun: 0 for pronoun in personal_pronouns}
        # Regex pattern to find personal pronouns, considering word boundaries
        pattern = r'\b(?:' + '|'.join(re.escape(pronoun) for pronoun in personal_pronouns) + r')\b'
        matches = re.findall(pattern,text, flags=re.IGNORECASE)
        overall_count = len(matches)
        df.at[index,'PERSONAL PRONOUNS'] = overall_count

        # Calculating avg. word length
        tchar = sum(len(word) for word in clean)
        if total_words==0:
            df.at[index,'AVG WORD LENGTH'] = 0
            
        else:
            awl= tchar/len(clean)
            avg_word_length = round(awl,2)
            df.at[index,'AVG WORD LENGTH'] = avg_word_length
            
        # writing the dataframe to the excel 
        df.to_excel(".\Output Data Structure.xlsx", index=False)
    
