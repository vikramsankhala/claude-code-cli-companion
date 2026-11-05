"""Chapter 39 example: chart_plotly.py. Run: python chart_plotly.py"""
import pandas as pd
import plotly.express as px
df = pd.read_csv("sales.csv")
fig = px.bar(df, x="month", y="revenue",
             color="region", barmode="group")
fig.write_html("revenue.html")
