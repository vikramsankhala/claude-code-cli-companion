"""Chapter 40 example. Run: streamlit run dashboard.py"""
import pandas as pd
import streamlit as st

st.title("Revenue by region")
f = st.file_uploader("Upload a sales CSV", type="csv")
if f:
    df = pd.read_csv(f)
    st.dataframe(df)
    st.bar_chart(df, x="month", y="revenue", color="region")
