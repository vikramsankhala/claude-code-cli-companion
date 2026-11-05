"""Chapter 39 example: crawl_page.py. Run: python crawl_page.py"""
import asyncio

from crawl4ai import AsyncWebCrawler


async def main():
    async with AsyncWebCrawler() as crawler:
        r = await crawler.arun(url="https://www.rbi.org.in")
        print(r.markdown[:800])

asyncio.run(main())
