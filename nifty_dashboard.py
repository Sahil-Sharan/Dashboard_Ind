import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.title("NIFTY50 Valuation Dashboard")

# ----------------------------
# Load NIFTY50 list from NSE
# ----------------------------
@st.cache_data
def load_nifty50():

    url = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"

    df = pd.read_csv(url)

    df["YahooSymbol"] = df["Symbol"] + ".NS"

    return df


nifty_df = load_nifty50()

stock = st.selectbox(
    "Select Stock",
    nifty_df["YahooSymbol"],
    format_func=lambda x: nifty_df[nifty_df["YahooSymbol"] == x]["Company Name"].values[0]
)

ticker = yf.Ticker(stock)
info = ticker.info

# ----------------------------
# Fundamental Metrics
# ----------------------------

current_price = info.get("currentPrice")
pe = info.get("trailingPE")
pb = info.get("priceToBook")
forward_pe = info.get("forwardPE")
target = info.get("targetMeanPrice")
opm = info.get("operatingMargins")
growth = info.get("earningsGrowth")

# PEG
if pe and growth:
    peg = pe / (growth * 100)
else:
    peg = None

# ----------------------------
# Bloomberg style metric panel
# ----------------------------

st.subheader("Key Metrics")

col1, col2, col3 = st.columns(3)

col1.metric("Current Price", current_price)
col2.metric("PE Ratio", pe)
col3.metric("PB Ratio", pb)

col4, col5, col6 = st.columns(3)

col4.metric("Forward PE", forward_pe)
col5.metric("PEG Ratio", peg)
col6.metric("OPM", f"{opm*100:.2f}%" if opm else "N/A")

st.metric("Average Target Price", target)

# ----------------------------
# Historic PE estimation
# ----------------------------

hist5y = ticker.history(period="5y")

if not hist5y.empty and pe:
    historic_pe = pe * (hist5y["Close"].mean() / hist5y["Close"].iloc[-1])
else:
    historic_pe = None

st.subheader("Historic PE Comparison")

st.write("Current PE:", pe)
st.write("Estimated Historic Mean PE:", historic_pe)

# ----------------------------
# Valuation signal
# ----------------------------

st.subheader("Valuation Signal")

if pe and historic_pe:

    if pe < historic_pe:
        st.success("Stock may be undervalued")

    elif pe < historic_pe * 1.2:
        st.warning("Stock fairly valued")

    else:
        st.error("Stock may be overvalued")

# ----------------------------
# Price chart
# ----------------------------

st.subheader("1 Year Price Chart")

hist = ticker.history(period="1y")

st.line_chart(hist["Close"])

# ----------------------------
# Recent Data
# ----------------------------

st.subheader("Recent Price Data")

st.dataframe(hist.tail(10))

# ----------------------------
# Screener holding pattern
# ----------------------------

st.subheader("Institutional Holding Trend (Last 3 Quarters)")

symbol = stock.replace(".NS","")

try:

    url = f"https://www.screener.in/company/{symbol}/"

    headers = {"User-Agent":"Mozilla/5.0"}

    html = requests.get(url,headers=headers).text

    tables = pd.read_html(html)

    holding = None

    for table in tables:
        if "Shareholding Pattern" in str(table):
            holding = table
            break

    if holding is not None:

        holding = holding.set_index(holding.columns[0])

        holding = holding.iloc[:, -3:]

        st.dataframe(holding)

        # Calculate change
        latest = holding.iloc[:, -1]
        prev = holding.iloc[:, -2]

        change = latest - prev

        st.subheader("3 Month Change")

        st.table(change)

    else:

        st.write("Holding pattern not found")

except:

    st.write("Could not load Screener holding data")
