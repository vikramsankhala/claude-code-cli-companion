"""Chapter 39 example: ask_claude.py. Run: python ask_claude.py"""
import anthropic
client = anthropic.Anthropic()   # reads ANTHROPIC_API_KEY
msg = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=500,
    messages=[{"role": "user",
               "content": "Explain KFS rules for a loan officer in 3 bullets."}],
)
print(msg.content[0].text)
