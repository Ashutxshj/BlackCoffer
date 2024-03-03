#!APPROACH
#? 1.A function to convert the links of csv files into usable links
#? 2.A function to extract article title and text and nothing else
#? 3.A for loop to do it for every link
#? 4.A function to make save the extracted data in a new text files with their "URL_ID" as their names
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def extract_links(url):
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        response = requests.get(url)
        response.raise_for_status()  #HTTPError for bad responses

        soup = BeautifulSoup(response.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True)]
        return links
    except requests.exceptions.RequestException as e:
        print(f"Error fetching links from {url}: {e}")
        return []

def extract_article(link):
    try:
        response = requests.get(link)
        response.raise_for_status()  #Exception for bad requests

        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.title.text.strip()

        
        article_text = ""
        paragraphs = soup.find_all('p')
        for paragraph in paragraphs:
            article_text += paragraph.text + "\n"

        return title, article_text

    except Exception as e:
        print(f"Error extracting article from {link}: {e}")
        return None, None

def scrape_and_store_data(excel_file_path):
    df = pd.read_excel(excel_file_path)

    for index, row in df.iterrows():
        website_url = row['URL']
        url_id = row['URL_ID']

        links = extract_links(website_url)

        print(f"Processing {len(links)} links for URL_ID {url_id}")

        for link in links:
            title, text = extract_article(link)
            if title and text:
                file_name = os.path.join(f"{url_id}_{link.replace('/', '_').replace(':', '_')}.txt")
                with open(file_name, 'w', encoding='utf-8') as file:
                    file.write(f"Title: {title}\n\nArticle Text:\n{text}\n\n")
                print(f"Saved {file_name}")
            else:
                print(f"Failed to extract article information from {link}.")

if __name__ == "__main__":
    excel_file_path = 'Input.xlsx'
    scrape_and_store_data(excel_file_path)



