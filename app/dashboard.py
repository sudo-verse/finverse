import streamlit as st
import json
import pandas as pd

st.title("📊 Market Intelligence Dashboard")

# Load signals
try:
    with open("signals.json", "r") as f:
        data = json.load(f)
except:
    data = []

df = pd.DataFrame(data)

if df.empty:
    st.warning("No data available yet")
else:
    st.dataframe(df)
st.subheader("📈 Signal Summary")

if not df.empty:
    buy_count = len(df[df["signal"].str.contains("BUY")])
    sell_count = len(df[df["signal"].str.contains("SELL")])

    st.write(f"BUY Signals: {buy_count}")
    st.write(f"SELL Signals: {sell_count}")
st.subheader("📊 Signal Distribution")

if not df.empty:
    st.bar_chart(df["signal"].value_counts())
signal_filter = st.selectbox("Filter by Signal", ["All", "BUY", "SELL", "HOLD"])

if signal_filter != "All":
    filtered_df = df[df["signal"].str.contains(signal_filter)]
else:
    filtered_df = df

st.dataframe(filtered_df)
if not df.empty:
    st.subheader("🧠 Latest Insights")

    for i, row in df.tail(5).iterrows():
        st.write(f"**{row['company']}** → {row['signal']}")
        st.write(row.get("event", "No event"))
        st.write("---")