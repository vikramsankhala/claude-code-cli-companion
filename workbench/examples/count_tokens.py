"""Chapter 39 example: count_tokens.py. Run: python count_tokens.py"""
import tiktoken
enc = tiktoken.get_encoding("o200k_base")
text = open("report.md", encoding="utf-8").read()
print(len(enc.encode(text)), "tokens (estimate)")
