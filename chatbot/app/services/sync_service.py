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

        full_text = " ".join(text_content)

        # Extract email addresses
        email_matches = re.findall(r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b', full_text)
        emails = list(set(email_matches))

        # Extract phone numbers (basic international + local pattern)
        phone_matches = re.findall(
            r'(\+?\d{1,3}[-.\s]??\(?\d{1,4}\)?[-.\s]??\d{2,4}[-.\s]??\d{3,5})', full_text)
        phones = list(set(phone_matches))

        if emails:
            text_content.append("\nEmails found:\n" + "\n".join(emails))
        if phones:
            text_content.append("\nPhone Numbers found:\n" + "\n".join(phones))

        return "\n".join(text_content)
    except Exception as e:
        print(f"[ERROR] Error scraping {url}: {e}")
        return ""
