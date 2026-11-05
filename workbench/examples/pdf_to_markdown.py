"""Chapter 38 example: pdf_to_markdown.py. Run: python pdf_to_markdown.py"""
import pymupdf4llm
md = pymupdf4llm.to_markdown("report.pdf")
open("report.md", "w", encoding="utf-8").write(md)
