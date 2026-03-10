import streamlit as st
import pandas as pd
import yfinance as yf


st.title("NIFTY50 Valuation Dashboard")

# Load NIFTY50 stocks automatically
@st.cache_data
def load_nifty50():

    url = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"

    df = pd.read_csv(url)

    df["YahooSymbol"] = df["Symbol"] + ".NS"

    return df


nifty_df = load_nifty50()

stock = st.selectbox(
    "Select NIFTY50 Stock",
    nifty_df["YahooSymbol"],
    format_func=lambda x: nifty_df[nifty_df["YahooSymbol"] == x]["Company Name"].values[0]
)

ticker = yf.Ticker(stock)
info = ticker.info


# Extract metrics
pe = info.get("trailingPE")
pb = info.get("priceToBook")
forward_pe = info.get("forwardPE")
target = info.get("targetMeanPrice")
opm = info.get("operatingMargins")
growth = info.get("earningsGrowth")


# Calculate PEG
if pe and growth:
    peg = pe / (growth * 100)
else:
    peg = None


metrics = pd.DataFrame({
    "Metric":[
        "PE Ratio",
        "PB Ratio",
        "Forward PE",
        "PEG Ratio",
        "Target Price",
        "Operating Profit Margin"
    ],
    "Value":[
        pe,
        pb,
        forward_pe,
        peg,
        target,
        opm
    ]
})


st.subheader("Valuation Metrics")
st.table(metrics)


# Beginner valuation signal
st.subheader("Valuation Signal")

if peg and peg < 1:
    st.success("Stock may be undervalued")

elif peg and peg < 1.5:
    st.warning("Stock fairly valued")

else:
    st.error("Stock may be expensive")


# Price chart
hist = ticker.history(period="1y")

st.subheader("1 Year Price Chart")
st.line_chart(hist["Close"])


st.subheader("Recent Data")
st.dataframe(hist.tail(10))
