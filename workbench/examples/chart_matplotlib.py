"""Chapter 40 example: chart_matplotlib.py. Run: python chart_matplotlib.py"""
import matplotlib.pyplot as plt
import pandas as pd
df = pd.read_csv("sales.csv")
fig, ax = plt.subplots(figsize=(6, 3.5))
for region, g in df.groupby("region"):
    ax.plot(g["month"], g["revenue"], marker="o", label=region)
ax.set_ylabel("Revenue (₹ lakh)")
ax.legend()
fig.savefig("revenue.png", dpi=200, bbox_inches="tight")
