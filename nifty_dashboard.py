import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.set_page_config(layout="wide")

st.title("Indian Stock Valuation Dashboard")

# -------------------------------------------------------
# Load NIFTY50 list
# -------------------------------------------------------

@st.cache_data
def load_nifty():

    url = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"

    df = pd.read_csv(url)

    df["YahooSymbol"] = df["Symbol"] + ".NS"

    return df

nifty = load_nifty()

stock = st.selectbox(
    "Select Stock",
    nifty["YahooSymbol"],
    format_func=lambda x: nifty[nifty["YahooSymbol"]==x]["Company Name"].values[0]
)

ticker = yf.Ticker(stock)

# -------------------------------------------------------
# Price history
# -------------------------------------------------------

@st.cache_data(ttl=3600)
def load_history(symbol):

    ticker = yf.Ticker(symbol)

    hist = ticker.history(period="5y")

    return hist

hist = load_history(stock)

current_price = hist["Close"].iloc[-1]

# -------------------------------------------------------
# Financials
# -------------------------------------------------------

@st.cache_data(ttl=3600)
def load_financials(symbol):

    t = yf.Ticker(symbol)

    income = t.income_stmt
    balance = t.balance_sheet
    cashflow = t.cashflow

    return income, balance, cashflow

income, balance, cashflow = load_financials(stock)

# -------------------------------------------------------
# Compute ratios
# -------------------------------------------------------

try:

    revenue_growth = (
        income.iloc[0,0] / income.iloc[0,1] - 1
    )

except:
    revenue_growth = None

try:

    roe = (
        income.loc["Net Income"].iloc[0] /
        balance.loc["Stockholders Equity"].iloc[0]
    )

except:
    roe = None

try:

    debt_equity = (
        balance.loc["Total Debt"].iloc[0] /
        balance.loc["Stockholders Equity"].iloc[0]
    )

except:
    debt_equity = None

# -------------------------------------------------------
# Buffett Quality Score
# -------------------------------------------------------

score = 0

if roe and roe > 0.15:
    score += 2

if revenue_growth and revenue_growth > 0.10:
    score += 2

if debt_equity and debt_equity < 0.5:
    score += 2

if cashflow is not None:
    score += 2

if income is not None:
    score += 2

# Score out of 10

st.subheader("Buffett Quality Score")

st.metric("Score", f"{score}/10")

if score >= 8:
    st.success("High Quality Business")

elif score >=5:
    st.warning("Average Quality")

else:
    st.error("Weak Business")

# -------------------------------------------------------
# Automatic Buy Zone
# -------------------------------------------------------

st.subheader("Automatic Buy Zone")

ma200 = hist["Close"].rolling(200).mean().iloc[-1]

buy_zone = ma200 * 0.9

sell_zone = ma200 * 1.2

col1,col2,col3 = st.columns(3)

col1.metric("Current Price", round(current_price,2))

col2.metric("Buy Zone", round(buy_zone,2))

col3.metric("Overvalued Zone", round(sell_zone,2))

if current_price < buy_zone:

    st.success("Stock in Buy Zone")

elif current_price < sell_zone:

    st.warning("Fair Value Range")

else:

    st.error("Overvalued")

# -------------------------------------------------------
# Price Chart
# -------------------------------------------------------

st.subheader("5 Year Price Chart")

st.line_chart(hist["Close"])

# -------------------------------------------------------
# FII DII FLOW
# -------------------------------------------------------

st.subheader("FII / DII Market Flow")

@st.cache_data(ttl=3600)
def fii_dii():

    url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"

    tables = pd.read_html(url)

    df = tables[0]

    return df

try:

    flow = fii_dii()

    st.dataframe(flow.head())

except:

    st.write("Could not load FII/DII data")

# -------------------------------------------------------
# Valuation Indicator
# -------------------------------------------------------

st.subheader("Valuation Indicator")

mean_price = hist["Close"].mean()

if current_price < mean_price * 0.8:

    st.success("Undervalued vs 5Y average")

elif current_price < mean_price * 1.2:

    st.warning("Fair Value")

else:

    st.error("Overvalued")

# -------------------------------------------------------
# Screener Shareholding
# -------------------------------------------------------

st.subheader("Shareholding Trend")

symbol = stock.replace(".NS","")

try:

    url = f"https://www.screener.in/company/{symbol}/consolidated/"

    headers = {"User-Agent":"Mozilla/5.0"}

    html = requests.get(url,headers=headers).text

    tables = pd.read_html(html)

    holding=None

    for table in tables:

        if table.columns[0]=="Shareholders":

            holding = table

            break

    if holding is not None:

        holding = holding.set_index("Shareholders")

        st.dataframe(holding)

    else:

        st.write("Holding data not found")

except:

    st.write("Error loading holding data")
