"""Chapter 39 example: polars_basics.py. Run: python polars_basics.py"""
import polars as pl
df = pl.read_csv("sales.csv")
print(df.group_by("region")
        .agg(pl.col("revenue").sum())
        .sort("region"))
