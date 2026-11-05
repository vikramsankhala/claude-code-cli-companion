"""Chapter 38 example: screenshot_page.py. Run: python screenshot_page.py"""
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto("https://solinexta-ai.org")
    page.screenshot(path="home.png", full_page=True)
    b.close()
