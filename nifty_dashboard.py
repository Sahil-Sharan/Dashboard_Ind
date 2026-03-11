import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.set_page_config(layout="wide", page_title="Indian Investor Terminal")

st.title("Indian Equity Investor Terminal")

# -----------------------------------------------------
# LOAD NIFTY STOCK LIST
# -----------------------------------------------------

@st.cache_data
def load_nifty():

    url="https://archives.nseindia.com/content/indices/ind_nifty50list.csv"
    df=pd.read_csv(url)
    df["YahooSymbol"]=df["Symbol"]+".NS"

    return df

nifty=load_nifty()

stock=st.selectbox(
    "Select Stock",
    nifty["YahooSymbol"],
    format_func=lambda x: nifty[nifty["YahooSymbol"]==x]["Company Name"].values[0]
)

ticker=yf.Ticker(stock)

# -----------------------------------------------------
# MARKET OVERVIEW
# -----------------------------------------------------

st.header("Market Overview")

col1,col2,col3=st.columns(3)

nifty_index=yf.Ticker("^NSEI")
nifty_hist=nifty_index.history(period="1y")

nifty_price=nifty_hist["Close"].iloc[-1]

nifty_ma200=nifty_hist["Close"].rolling(200).mean().iloc[-1]

col1.metric("NIFTY50",round(nifty_price,2))
col2.metric("200 Day Avg",round(nifty_ma200,2))

if nifty_price<nifty_ma200*0.9:
    col3.success("Market undervalued")

elif nifty_price<nifty_ma200*1.1:
    col3.warning("Market fairly valued")

else:
    col3.error("Market overvalued")

# -----------------------------------------------------
# STOCK DATA
# -----------------------------------------------------

hist=ticker.history(period="5y")
price=hist["Close"].iloc[-1]

info={}

try:
    data=ticker.get_info()

    info["pe"]=data.get("trailingPE")
    info["fpe"]=data.get("forwardPE")
    info["pb"]=data.get("priceToBook")
    info["div"]=data.get("dividendYield")
    info["target"]=data.get("targetMeanPrice")
    info["opm"]=data.get("operatingMargins")
    info["roe"]=data.get("returnOnEquity")
    info["growth"]=data.get("earningsGrowth")
    info["sector"]=data.get("sector")

except:
    pass

# PEG
peg=None
if info["pe"] and info["growth"]:
    peg=info["pe"]/(info["growth"]*100)

# -----------------------------------------------------
# KEY METRICS PANEL
# -----------------------------------------------------

st.header("Stock Valuation")

c1,c2,c3,c4,c5,c6=st.columns(6)

c1.metric("Price",round(price,2))
c2.metric("PE",info["pe"])
c3.metric("Forward PE",info["fpe"])
c4.metric("PB",info["pb"])
c5.metric("Dividend Yield",
          f"{info['div']*100:.2f}%" if info["div"] else None)
c6.metric("Target Price",info["target"])

c7,c8,c9=st.columns(3)

c7.metric("PEG Ratio",peg)
c8.metric("ROE",f"{info['roe']*100:.2f}%" if info["roe"] else None)
c9.metric("Operating Margin",
          f"{info['opm']*100:.2f}%" if info["opm"] else None)

# -----------------------------------------------------
# QUALITY + VALUATION
# -----------------------------------------------------

col1,col2=st.columns(2)

# Buffett score
score=0

if info["roe"] and info["roe"]>0.15:
    score+=2

if info["opm"] and info["opm"]>0.15:
    score+=2

if info["pe"] and info["pe"]<25:
    score+=2

if info["pb"] and info["pb"]<5:
    score+=2

if info["div"]:
    score+=2

with col1:

    st.subheader("Buffett Quality Score")

    st.metric("Score",f"{score}/10")

    if score>=8:
        st.success("High Quality")

    elif score>=5:
        st.warning("Average")

    else:
        st.error("Weak")

# buy zone
with col2:

    st.subheader("Automatic Buy Zone")

    ma200=hist["Close"].rolling(200).mean().iloc[-1]

    buy_zone=ma200*0.9
    sell_zone=ma200*1.2

    st.metric("Buy Price",round(buy_zone,2))

    if price<buy_zone:
        st.success("Undervalued")

    elif price<sell_zone:
        st.warning("Fair Value")

    else:
        st.error("Overvalued")

# -----------------------------------------------------
# PRICE CHART
# -----------------------------------------------------

st.header("Price Trend")

st.line_chart(hist["Close"])

# -----------------------------------------------------
# SECTOR COMPARISON
# -----------------------------------------------------

st.header("Sector Comparison")

sector_stocks=nifty[nifty["YahooSymbol"]!=stock].head(10)

sector_data=[]

for s in sector_stocks["YahooSymbol"]:

    try:

        t=yf.Ticker(s)

        i=t.get_info()

        sector_data.append({
            "stock":s,
            "PE":i.get("trailingPE"),
            "PB":i.get("priceToBook"),
        })

    except:
        pass

sector_df=pd.DataFrame(sector_data)

st.dataframe(sector_df)

# -----------------------------------------------------
# FII / DII FLOW
# -----------------------------------------------------

st.header("Institutional Flow")

try:

    fii=pd.read_html(
        "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
    )[0]

    st.dataframe(fii)

except:
    st.write("FII/DII data unavailable")

# -----------------------------------------------------
# SHAREHOLDING
# -----------------------------------------------------

st.header("Shareholding Pattern")

symbol=stock.replace(".NS","")

try:

    url=f"https://www.screener.in/company/{symbol}/consolidated/"

    headers={"User-Agent":"Mozilla/5.0"}

    html=requests.get(url,headers=headers).text

    tables=pd.read_html(html)

    holding=None

    for table in tables:

        if table.columns[0]=="Shareholders":

            holding=table
            break

    if holding is not None:

        holding=holding.set_index("Shareholders")

        st.dataframe(holding)

except:

    st.write("Shareholding data unavailable")
