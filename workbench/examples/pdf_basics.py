"""Chapter 39 example: pdf_basics.py. Run: python pdf_basics.py"""
import pymupdf
doc = pymupdf.open("book.pdf")
print(doc.page_count, "pages")
print(doc[0].get_text()[:500])
