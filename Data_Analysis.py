import concurrent.futures
import requests
from bs4 import BeautifulSoup
import pandas as pd
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import re

# Download NLTK resources
import nltk
nltk.download('stopwords')
nltk.download('punkt')

# Load stopwords
stop_words = set(stopwords.words('english'))

def extract_links(url):
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True)]
        return links
    except requests.exceptions.RequestException as e:
        print(f"Error fetching links from {url}: {e}")
        return []

def extract_article(link):
    try:
        response = requests.get(link)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.text.strip()
        article_text = ""
        paragraphs = soup.find_all('p')
        for paragraph in paragraphs:
            article_text += paragraph.text + "\n"
        return title, article_text
    except Exception as e:
        print(f"Error: {e}")
        return None, None

def scrape_and_analyze_data_parallel(excel_file_path, output_excel_path):
    df = pd.read_excel(excel_file_path)

    final_report_df = pd.DataFrame()

    def process_url(row):
        website_url = row['URL']
        url_id = row['URL_ID']
        links = extract_links(website_url)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(extract_article, links))

        with open(f"Data.txt", 'w', encoding='utf-8') as file:
            for title, text in results:
                if title and text:
                    file.write(f"Title: {title}\n")
                    file.write("\nArticle Text:\n")
                    file.write(text + "\n\n")
                else:
                    file.write(f"Failed to extract article information.\n")

        file_path = 'Data.txt'
        try:
            report_df = read_and_analyze_data(file_path)
        except FileNotFoundError:
            report_df = pd.DataFrame(columns=['Title'])

        if 'Title' not in report_df.columns:
            return

        report_df['URL_ID'] = url_id

        nonlocal final_report_df
        final_report_df = pd.concat([final_report_df, report_df], ignore_index=True)

    df.apply(process_url, axis=1)

    final_report_df.to_excel(output_excel_path, index=False)

def clean_and_tokenize(text):
    text = re.sub("[^a-zA-Z]", " ", text)
    tokens = word_tokenize(text.lower())
    tokens = [word for word in tokens if word not in stop_words]
    return tokens

def analyze_article(title, text):
    tokens = clean_and_tokenize(text)
    try:
        positive_words = set(pd.read_csv('StopWords/positive-words.txt', header=None, on_bad_lines='skip')[0])
        negative_words = set(pd.read_csv('StopWords/negative-words.txt', header=None, on_bad_lines='skip')[0])
    except FileNotFoundError:
        positive_words = set()
        negative_words = set()

    positive_score = sum(1 for word in tokens if word in positive_words)
    negative_score = sum(1 for word in tokens if word in negative_words)

    polarity_score = (positive_score - negative_score) / ((positive_score + negative_score) + 0.000001)
    subjectivity_score = (positive_score + negative_score) / (len(tokens) + 0.000001)

    sentence_tokens = sent_tokenize(text)
    total_words = len(tokens)
    total_sentences = len(sentence_tokens)

    average_sentence_length = total_words / total_sentences

    complex_words = [word for word in tokens if len(word) > 2]
    percentage_complex_words = len(complex_words) / total_words

    fog_index = 0.4 * (average_sentence_length + percentage_complex_words)

    average_words_per_sentence = total_words / total_sentences
    complex_word_count = len(complex_words)
    word_count = total_words

    personal_pronouns = sum(1 for word in tokens if word.lower() in ["i", "we", "my", "ours", "us"])

    average_word_length = sum(len(word) for word in tokens) / total_words

    report_df = pd.DataFrame({
        'Title': [title],
        'Polarity Score': [polarity_score],
        'Subjectivity Score': [subjectivity_score],
        'Average Sentence Length': [average_sentence_length],
        'Percentage of Complex Words': [percentage_complex_words],
        'Fog Index': [fog_index],
        'Average Words Per Sentence': [average_words_per_sentence],
        'Complex Word Count': [complex_word_count],
        'Word Count': [word_count],
        'Personal Pronouns Count': [personal_pronouns],
        'Average Word Length': [average_word_length]
    })

    return report_df

def read_and_analyze_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    articles = re.split(r'Title:', content)[1:]
    final_report_df = pd.DataFrame()

    for article in articles:
        title, text = article.split('\n', 1)
        report_df = analyze_article(title.strip(), text.strip())
        if 'Title' not in report_df.columns:
            continue
        final_report_df = pd.concat([final_report_df, report_df], ignore_index=True)

    return final_report_df

if __name__ == "__main__":
    excel_file_path = 'Input.xlsx'
    output_excel_path = 'Output Data Structure.xlsx'
    
    scrape_and_analyze_data_parallel(excel_file_path, output_excel_path)
