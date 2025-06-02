#!/usr/bin/env python3
import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urlunparse
from datetime import datetime
from hashlib import md5

class WebsiteScraper:
    def __init__(self, base_url, max_pages=1000):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls = set()
        self.text_hashes = set()
        self.text_content = []
        self.max_pages = max_pages
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }

    def normalize_url(self, url):
        parsed = urlparse(url)
        return urlunparse(parsed._replace(query="", fragment=""))

    def is_valid_url(self, url):
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.netloc == self.domain

    def get_all_links(self, soup, page_url):
        links = []
        for anchor in soup.find_all('a', href=True):
            link = anchor['href']
            if not link.startswith('http'):
                link = urljoin(page_url, link)
            normalized = self.normalize_url(link)
            if self.is_valid_url(normalized) and normalized not in self.visited_urls:
                links.append(normalized)
        return links

    def extract_text(self, soup):
        for script_or_style in soup(['script', 'style', 'header', 'footer', 'nav']):
            script_or_style.decompose()
        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return '\n'.join(chunk for chunk in chunks if chunk)

    def scrape_page(self, url):
        try:
            print(f"Scraping: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            if 'text/html' not in response.headers.get('Content-Type', '').lower():
                return [], ""

            soup = BeautifulSoup(response.text, 'html.parser')
            text = self.extract_text(soup)
            links = self.get_all_links(soup, url)

            return links, text
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return [], ""

    def scrape_website(self):
        urls_to_visit = [self.base_url]

        while urls_to_visit and len(self.visited_urls) < self.max_pages:
            url = urls_to_visit.pop(0)
            normalized_url = self.normalize_url(url)

            if normalized_url in self.visited_urls:
                continue

            self.visited_urls.add(normalized_url)
            links, text = self.scrape_page(url)

            if not text.strip():
                continue

            content_hash = md5(text.encode('utf-8')).hexdigest()
            if content_hash in self.text_hashes:
                continue

            self.text_hashes.add(content_hash)
            page_content = f"\n\n=== {normalized_url} ===\n{text}"
            self.text_content.append(page_content)

            time.sleep(0.5)
            urls_to_visit.extend(links)

    def save_to_file(self, filename=None):
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            domain_name = self.domain.replace('.', '_')
            filename = f"{domain_name}_{timestamp}.txt"

        output_dir = os.path.expanduser("~/website_scrapes")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)

        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(f"Website Scrape: {self.base_url}\n")
            file.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write(f"Pages scraped: {len(self.visited_urls)}\n")
            file.write("="*80 + "\n\n")
            for content in self.text_content:
                file.write(content + "\n")

        print(f"\n✅ Scraping completed!")
        print(f"📄 Pages scraped: {len(self.visited_urls)}")
        print(f"📁 Results saved to: {output_path}")
        return output_path


def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def main():
    print("\n===== Website Text Scraper (Improved) =====\n")

    while True:
        domain = input("Enter the website domain to scrape (e.g., example.com): ")
        if not domain.startswith("http://") and not domain.startswith("https://"):
            url = "https://" + domain
        else:
            url = domain

        if validate_url(url):
            break
        else:
            print("⚠️ Invalid domain. Please try again.")

    scraper = WebsiteScraper(url)
    print(f"\n🚀 Starting to scrape {url}")
    print("This may take some time... Press Ctrl+C to stop\n")

    try:
        scraper.scrape_website()
        output_file = scraper.save_to_file()

        if input("\nOpen output file? (y/n): ").lower() == 'y':
            os.system(f"open {output_file}")

    except KeyboardInterrupt:
        print("\n⛔ Scraping interrupted by user. Saving data...")
        scraper.save_to_file()
        print("✅ Done!")

if __name__ == "__main__":
    main()
