"""Chapter 40 example: pandas_basics.py. Run: python pandas_basics.py"""
import pandas as pd
df = pd.read_csv("sales.csv")
print(df.groupby("region")["revenue"].sum())
print(df.pivot_table(index="month", columns="region", values="revenue"))
