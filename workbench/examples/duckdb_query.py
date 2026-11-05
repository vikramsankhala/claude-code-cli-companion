"""Chapter 40 example: duckdb_query.py. Run: python duckdb_query.py"""
import duckdb

print(duckdb.sql("""
    SELECT region, SUM(revenue) AS total
    FROM 'sales.csv'
    GROUP BY region ORDER BY total DESC
""").df())
