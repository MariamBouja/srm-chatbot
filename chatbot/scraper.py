import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse

OUTPUT_DIR = Path("data/website")
SITEMAP_URLS = [
    "https://www.srm-sm.ma/wp-sitemap-posts-page-1.xml",
]

SKIP_KEYWORDS = [
    "sample-page", "homepage", "about-us", "blog", "shop", "cart",
    "checkout", "my-account", "project-style", "our-team"
]


def slug_from_url(url):
    path = urlparse(url).path.strip("/")
    return path if path else "accueil"


def clean_filename(name):
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    return name[:80]


def get_urls_from_sitemap(sitemap_url):
    response = requests.get(sitemap_url, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "xml")
    urls = []

    for loc in soup.find_all("loc"):
        url = loc.get_text(strip=True)

        if not any(skip in url for skip in SKIP_KEYWORDS):
            urls.append(url)

    return urls


def clean_text(text):
    unwanted_lines = [
        "Skip to content",
        "Search",
        "Search for:",
        "Copyright © 2024 SRM All Rights Reserved.",
        "*",
    ]

    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    lines = [line for line in lines if line not in unwanted_lines]

    return "\n".join(lines)

def scrape_page(url):
    print(f"Scraping: {url}")

    response = requests.get(url, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "form"]):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else slug_from_url(url)
    text = clean_text(soup.get_text())

    if len(text) < 100:
        print(f"Skipped empty/weak page: {url}")
    return

    content = f"""URL: {url}
TITLE: {title}

{text}
"""

    filename = clean_filename(slug_from_url(url)) + ".txt"
    file_path = OUTPUT_DIR / filename
    file_path.write_text(content, encoding="utf-8")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_urls = []

    for sitemap_url in SITEMAP_URLS:
        all_urls.extend(get_urls_from_sitemap(sitemap_url))

    print(f"URLs found: {len(all_urls)}")

    for url in all_urls:
        try:
            scrape_page(url)
        except Exception as e:
            print(f"Error scraping {url}: {e}")

    print("Done.")


if __name__ == "__main__":
    main()