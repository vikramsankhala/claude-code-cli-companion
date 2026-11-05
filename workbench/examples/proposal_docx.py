"""Chapter 39 example: proposal_docx.py. Run: python proposal_docx.py"""
from docx import Document
doc = Document()
doc.add_heading("Programme proposal", level=1)
doc.add_paragraph("Participants leave with working assets, not just notes.")
t = doc.add_table(rows=1, cols=2)
t.style = "Light Grid Accent 1"
t.rows[0].cells[0].text, t.rows[0].cells[1].text = "Module", "Days"
row = t.add_row().cells
row[0].text, row[1].text = "Agentic coding", "2"
doc.save("proposal.docx")
