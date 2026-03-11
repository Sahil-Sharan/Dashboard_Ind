import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.set_page_config(page_title="Indian Investor Terminal", layout="wide")

st.title("Indian Equity Investor Terminal")

# ---------------------------------------------------
# Load NIFTY50
# ---------------------------------------------------

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

# ---------------------------------------------------
# PRICE HISTORY
# ---------------------------------------------------

hist = ticker.history(period="5y")

price = hist["Close"].iloc[-1]

# ---------------------------------------------------
# BASIC INFO
# ---------------------------------------------------

try:
    data = ticker.get_info()
except:
    data = {}

pe = data.get("trailingPE")
fpe = data.get("forwardPE")
pb = data.get("priceToBook")
target_mean = data.get("targetMeanPrice")
target_high = data.get("targetHighPrice")
target_low = data.get("targetLowPrice")
analysts = data.get("numberOfAnalystOpinions")
roe = data.get("returnOnEquity")
opm = data.get("operatingMargins")
growth = data.get("earningsGrowth")
sector = data.get("sector")

# ---------------------------------------------------
# DIVIDEND YIELD (CORRECT)
# ---------------------------------------------------

div_rate = data.get("dividendRate")

if div_rate and price:
    div_yield = (div_rate / price) * 100
else:
    div_yield = None

# ---------------------------------------------------
# PEG RATIO
# ---------------------------------------------------

if pe and growth:
    peg = pe / (growth * 100)
else:
    peg = None

# ---------------------------------------------------
# UPSIDE / DOWNSIDE
# ---------------------------------------------------

if target_mean and price:
    upside = ((target_mean - price) / price) * 100
else:
    upside = None

# ---------------------------------------------------
# HEADER METRICS
# ---------------------------------------------------

st.subheader("Key Metrics")

c1,c2,c3,c4,c5,c6 = st.columns(6)

c1.metric("Price", round(price,2))
c2.metric("PE", pe)
c3.metric("Forward PE", fpe)
c4.metric("PB", pb)
c5.metric("Dividend Yield", f"{div_yield:.2f}%" if div_yield else None)
c6.metric("PEG", peg)

# ---------------------------------------------------
# TARGET PANEL
# ---------------------------------------------------

st.subheader("Analyst Target")

t1,t2,t3,t4 = st.columns(4)

t1.metric("Average Target", target_mean)
t2.metric("High Target", target_high)
t3.metric("Low Target", target_low)
t4.metric("Potential Upside", f"{upside:.2f}%" if upside else None)

st.write("Analyst Coverage:", analysts)

# ---------------------------------------------------
# BUFFETT QUALITY SCORE
# ---------------------------------------------------

score = 0

if roe and roe > 0.15:
    score += 2

if opm and opm > 0.15:
    score += 2

if pe and pe < 25:
    score += 2

if pb and pb < 5:
    score += 2

if div_yield and div_yield > 1:
    score += 2

st.subheader("Buffett Quality Score")

st.metric("Score", f"{score}/10")

if score >= 8:
    st.success("High Quality Business")

elif score >=5:
    st.warning("Average Quality")

else:
    st.error("Weak Quality")

# ---------------------------------------------------
# BUY ZONE
# ---------------------------------------------------

st.subheader("Valuation Signal")

ma200 = hist["Close"].rolling(200).mean().iloc[-1]

buy_zone = ma200 * 0.9
sell_zone = ma200 * 1.2

b1,b2,b3 = st.columns(3)

b1.metric("200 DMA", round(ma200,2))
b2.metric("Buy Zone", round(buy_zone,2))
b3.metric("Overvalued Zone", round(sell_zone,2))

if price < buy_zone:
    st.success("Stock in BUY zone")

elif price < sell_zone:
    st.warning("Stock fairly valued")

else:
    st.error("Stock overvalued")

# ---------------------------------------------------
# DCF INTRINSIC VALUE
# ---------------------------------------------------

st.subheader("Intrinsic Value (DCF Model)")

try:
    cashflow = ticker.cashflow
    fcf = cashflow.loc["Free Cash Flow"].iloc[0]

    growth_rate = 0.12
    discount = 0.10

    intrinsic = 0

    for t in range(1,11):
        intrinsic += (fcf*(1+growth_rate)**t)/(1+discount)**t

    shares = data.get("sharesOutstanding")

    intrinsic_per_share = intrinsic / shares

    mos = ((intrinsic_per_share - price) / intrinsic_per_share) * 100

    d1,d2 = st.columns(2)

    d1.metric("Intrinsic Value", round(intrinsic_per_share,2))
    d2.metric("Margin of Safety", f"{mos:.2f}%")

except:
    st.write("DCF data unavailable")

# ---------------------------------------------------
# PRICE CHART
# ---------------------------------------------------

st.subheader("5 Year Price Trend")

st.line_chart(hist["Close"])

# ---------------------------------------------------
# NIFTY MARKET GAUGE
# ---------------------------------------------------

st.subheader("Market Valuation (NIFTY)")

nifty_index = yf.Ticker("^NSEI")

nifty_hist = nifty_index.history(period="1y")

nifty_price = nifty_hist["Close"].iloc[-1]

nifty_ma = nifty_hist["Close"].rolling(200).mean().iloc[-1]

m1,m2,m3 = st.columns(3)

m1.metric("NIFTY", round(nifty_price,2))
m2.metric("200 DMA", round(nifty_ma,2))

if nifty_price < nifty_ma*0.9:
    m3.success("Market undervalued")

elif nifty_price < nifty_ma*1.1:
    m3.warning("Market fairly valued")

else:
    m3.error("Market overvalued")

# ---------------------------------------------------
# FII / DII FLOW
# ---------------------------------------------------

st.subheader("FII / DII Activity")

try:
    fii = pd.read_html(
        "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
    )[0]

    st.dataframe(fii)

except:
    st.write("Could not load institutional flow")

# ---------------------------------------------------
# SHAREHOLDING
# ---------------------------------------------------

st.subheader("Shareholding Pattern")

symbol = stock.replace(".NS","")

try:

    url = f"https://www.screener.in/company/{symbol}/consolidated/"

    headers = {"User-Agent":"Mozilla/5.0"}

    html = requests.get(url,headers=headers).text

    tables = pd.read_html(html)

    holding = None

    for table in tables:

        if table.columns[0] == "Shareholders":
            holding = table
            break

    if holding is not None:

        holding = holding.set_index("Shareholders")

        st.dataframe(holding)

    else:
        st.write("Shareholding data not found")

except:
    st.write("Could not load shareholding")

# ---------------------------------------------------
# SECTOR PE SNAPSHOT
# ---------------------------------------------------

st.subheader("Peer Valuation Snapshot")

peer_data = []

for s in nifty["YahooSymbol"].head(10):

    try:
        t = yf.Ticker(s)
        i = t.get_info()

        peer_data.append({
            "Stock": s,
            "PE": i.get("trailingPE"),
            "PB": i.get("priceToBook")
        })

    except:
        pass

peer_df = pd.DataFrame(peer_data)

st.dataframe(peer_df)
