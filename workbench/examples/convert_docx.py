"""Chapter 39 example: convert_docx.py. Run: python convert_docx.py"""
from markitdown import MarkItDown
md = MarkItDown()
result = md.convert("proposal.docx")
open("proposal.md", "w", encoding="utf-8").write(result.text_content)
