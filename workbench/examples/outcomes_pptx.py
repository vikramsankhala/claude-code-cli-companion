"""Chapter 39 example: outcomes_pptx.py. Run: python outcomes_pptx.py"""
from pptx import Presentation
prs = Presentation()
s = prs.slides.add_slide(prs.slide_layouts[1])
s.shapes.title.text = "Three outcomes this quarter"
body = s.placeholders[1].text_frame
body.text = "Working assets for every participant"
for line in ["Train-the-trainer layer", "Governance built in"]:
    body.add_paragraph().text = line
prs.save("outcomes.pptx")
