"""Chapter 39 example: github_api.py. Run: python github_api.py"""
import httpx

r = httpx.get("https://api.github.com/users/vikramsankhala")
r.raise_for_status()
print(r.json()["public_repos"])
