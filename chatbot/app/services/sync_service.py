import requests
from bs4 import BeautifulSoup
import re

def scrape_website(url):
    """
    Scrape visible text content from a given URL.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for tag in soup(['script', 'style']):
            tag.extract()

        text_content = []
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div']):
            text = tag.get_text(strip=True)
            if text:
                cleaned_text = re.sub(r'\s+', ' ', text)
                text_content.append(cleaned_text)

        return "\n".join(text_content)
    except Exception as e:
        print(f"[ERROR] Error scraping {url}: {e}")
        return ""
