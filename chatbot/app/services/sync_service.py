import requests
from bs4 import BeautifulSoup
import re
import json

def scrape_website(url):
    """
    Scrape visible text and footer information from a given URL.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove unwanted tags
        for tag in soup(['script', 'style']):
            tag.extract()

        text_content = []
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div',]):
            text = tag.get_text(strip=True)
            if text:
                cleaned_text = re.sub(r'\s+', ' ', text)
                text_content.append(cleaned_text)

        # Add footer info as JSON string
        footer_data = scrape_footer_info(soup)
        print("[INFO] Footer data:", footer_data)
        
        if footer_data:
            footer_lines = []
            for key, values in footer_data.items():
                if values:
                    footer_lines.append(f"{key.capitalize()}:")
                    footer_lines.extend(values)
            text_content.append("\n".join(footer_lines))
        print("[INFO] Text content:", text_content)
        return "\n".join(text_content)

    except Exception as e:
        print(f"[ERROR] Error scraping {url}: {e}")
        return ""

def scrape_footer_info(soup):
    """
    Extract footer information from a BeautifulSoup object.
    """
    try:
        footer = soup.find('footer')
        if not footer:
            print("[INFO] No <footer> tag found.")
            return {}

        for tag in footer(['script', 'style']):
            tag.decompose()

     
        addresses = []
        emails = []
        phones = []

        text = footer.get_text()

        # Extract emails and phone numbers
        emails = list(set(re.findall(r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b', text)))
        phones = list(set(re.findall(r'(\+?\d{1,3}[-.\s]??\(?\d{1,4}\)?[-.\s]??\d{2,4}[-.\s]??\d{3,5})', text)))

        # Extract addresses from <address> tags
        for addr in footer.find_all('address'):
            addr_text = addr.get_text(strip=True)
            if addr_text:
                addresses.append(addr_text)
        # for link in footer.select('ul li a[href]'):
        #     link_text = link.get_text(strip=True)
        #     href = link['href']
        #     if any(keyword in href.lower() for keyword in ["about", "contact", "blog", "career"]):
        #         data["quick_links"].append({"text": link_text, "url": href})
        #     elif any(keyword in href.lower() for keyword in ["development", "design"]):
        #         data["services"].append({"text": link_text, "url": href})

        # for social in footer.select('.social a[href]'):
        #     href = social.get('href')
        #     icon = social.find('img') or social.find('i')
        #     label = icon.get('alt') if icon and icon.has_attr('alt') else icon.get('class')[0] if icon else href
        #     data["social_links"].append({"platform": label, "url": href})

        return {
    "emails": emails,
    "phones": phones,
    "addresses": addresses
}

    except Exception as e:
        print(f"[ERROR] {e}")
        return {}
