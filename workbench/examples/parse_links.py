"""Chapter 39 example: parse_links.py. Run: python parse_links.py"""
import requests
from bs4 import BeautifulSoup

html = requests.get("https://example.com", timeout=20).text
soup = BeautifulSoup(html, "lxml")
for a in soup.select("a[href]"):
    print(a.get_text(strip=True), a["href"])
