import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path

BASE_URL = "https://www.srm-sm.ma/"
OUTPUT_FILE = Path("data/website/srm_website.txt")

visited = set()
texts = []


def is_valid_url(url):
    parsed = urlparse(url)
    return parsed.netloc == "www.srm-sm.ma" and url.startswith(BASE_URL)


def clean_text(text):
    lines = text.splitlines()
    lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(lines)


def scrape_page(url, depth=0, max_depth=2):
    if url in visited or depth > max_depth:
        return

    print(f"Scraping: {url}")
    visited.add(url)

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    page_text = clean_text(soup.get_text())

    if page_text:
        texts.append(f"\n\n===== PAGE: {url} =====\n\n{page_text}")

    links = soup.find_all("a", href=True)

    for link in links:
        next_url = urljoin(url, link["href"]).split("#")[0]

        if is_valid_url(next_url):
            scrape_page(next_url, depth + 1, max_depth)


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    scrape_page(BASE_URL)

    OUTPUT_FILE.write_text("\n".join(texts), encoding="utf-8")

    print("\nDone.")
    print(f"Pages scraped: {len(visited)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()