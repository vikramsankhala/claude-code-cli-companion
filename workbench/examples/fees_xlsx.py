"""Chapter 39 example: fees_xlsx.py. Run: python fees_xlsx.py"""
from openpyxl import Workbook
from openpyxl.styles import Font
wb = Workbook(); ws = wb.active; ws.title = "Fees"
ws.append(["Module", "Days", "Rate (₹/day)", "Total"])
ws.append(["Agentic coding", 2, 75000, "=B2*C2"])
ws.append(["Claude Code labs", 3, 75000, "=B3*C3"])
ws["D4"] = "=SUM(D2:D3)"
for c in ws[1]: c.font = Font(bold=True)
wb.save("fees.xlsx")
