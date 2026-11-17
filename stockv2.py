import requests
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "9130021718:AAE-BcPfkWwWrgjAz850FFJ0l82j4wZzkF0"  # Replace with your BotFather token
TELEGRAM_CHAT_ID = "8224498772"      # Replace with your numeric Chat ID
TOTAL_CAPITAL = 500000                      # ₹5 Lakhs total capital base
MAX_RISK_PER_TRADE = 7500                   # 1.5% strict risk rule (₹7,500)

# --- MULTI-PORTAL RSS NEWS SOURCES ---
NEWS_FEEDS = [
    "https://www.moneycontrol.com/rss/business.xml",
    "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
    "https://www.business-standard.com/rss/home_page_top_stories.rss",
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"
]

@st.cache_data(ttl=600)
def fetch_live_news():
    """Fetches and parses live headlines from major financial portals."""
    all_headlines = []
    for url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:25]:
                all_headlines.append({
                    "title": entry.title.lower(),
                    "raw_title": entry.title,
                    "link": entry.link
                })
        except Exception as e:
            print(f"Error fetching RSS feed {url}: {e}")
    return all_headlines

@st.cache_data(ttl=300)
def check_market_regime():
    """Macro Filter: Checks if Nifty 50 is bullish (above its 50 EMA)."""
    try:
        nifty = yf.download("^NSEI", period="3mo", interval="1d", progress=False)
        if nifty is None or nifty.empty:
            return True  # Default fallback if fetch fails
        if isinstance(nifty.columns, pd.MultiIndex):
            nifty.columns = nifty.columns.get_level_values(0)
        nifty['EMA_50'] = nifty['Close'].ewm(span=50, adjust=False).mean()
        last_close = float(nifty['Close'].iloc[-1])
        last_ema50 = float(nifty['EMA_50'].iloc[-1])
        return last_close > last_ema50
    except Exception:
        return True

# --- FULL 40-STOCK WATCHLIST (8 Sectors x 5 Stocks) ---
WATCHLIST = {
    # 1. Auto & EV
    "Auto: Tata Motors": {"ticker": "TATAMOTORS.NS", "keywords": ["tata motors", "jlr"]},
    "Auto: M&M": {"ticker": "M&M.NS", "keywords": ["mahindra", "m&m"]},
    "Auto: Bajaj Auto": {"ticker": "BAJAJ-AUTO.NS", "keywords": ["bajaj auto", "chetak"]},
    "Auto: TVS Motor": {"ticker": "TVSMOTOR.NS", "keywords": ["tvs motor", "tvs"]},
    "Auto: Tube Investments": {"ticker": "TIINDIA.NS", "keywords": ["tube investments", "tiindia"]},
    
    # 2. Defense
    "Defense: BEL": {"ticker": "BEL.NS", "keywords": ["bharat electronics", "bel"]},
    "Defense: HAL": {"ticker": "HAL.NS", "keywords": ["hindustan aeronautics", "hal"]},
    "Defense Ship: Mazdock": {"ticker": "MAZDOCK.NS", "keywords": ["mazagon dock", "mazdock"]},
    "Defense: BDL": {"ticker": "BDL.NS", "keywords": ["bharat dynamics", "bdl"]},
    "Defense: Zen Tech": {"ticker": "ZENTEC.NS", "keywords": ["zen technologies", "zen tech"]},
    
    # 3. Power & Renewables
    "Power: Tata Power": {"ticker": "TATAPOWER.NS", "keywords": ["tata power"]},
    "Power: Suzlon": {"ticker": "SUZLON.NS", "keywords": ["suzlon"]},
    "Power: NTPC Green": {"ticker": "NTPCGREEN.NS", "keywords": ["ntpc green", "ntpc"]},
    "Power: Adani Green": {"ticker": "ADANIGREEN.NS", "keywords": ["adani green"]},
    "Power: Inox Wind": {"ticker": "INOXWIND.NS", "keywords": ["inox wind"]},
    
    # 4. Marine & Logistics
    "Marine: Adani Ports": {"ticker": "ADANIPORTS.NS", "keywords": ["adani ports", "mundra"]},
    "Marine: GE Shipping": {"ticker": "GESHIPPING.NS", "keywords": ["ge shipping", "great eastern"]},
    "Marine: Concor": {"ticker": "CONCOR.NS", "keywords": ["concor", "container corporation"]},
    "Marine: SCI": {"ticker": "SCI.NS", "keywords": ["shipping corporation", "sci"]},
    "Marine: Allcargo": {"ticker": "ALLCARGO.NS", "keywords": ["allcargo"]},
    
    # 5. Pharma & Healthcare
    "Pharma: Sun Pharma": {"ticker": "SUNPHARMA.NS", "keywords": ["sun pharma", "sun pharmaceutical"]},
    "Pharma: Dr Reddy": {"ticker": "DRREDDY.NS", "keywords": ["dr reddy", "dr. reddy"]},
    "Pharma: Cipla": {"ticker": "CIPLA.NS", "keywords": ["cipla"]},
    "Pharma: Divis Lab": {"ticker": "DIVISLAB.NS", "keywords": ["divis laboratories", "divi's"]},
    "Pharma: Alkem Labs": {"ticker": "ALKEM.NS", "keywords": ["alkem"]},
    
    # 6. IT & Technology
    "IT: TCS": {"ticker": "TCS.NS", "keywords": ["tcs", "tata consultancy"]},
    "IT: Infosys": {"ticker": "INFY.NS", "keywords": ["infosys", "infy"]},
    "IT: HCL Tech": {"ticker": "HCLTECH.NS", "keywords": ["hcl tech", "hcltechnologies"]},
    "IT: Tech Mahindra": {"ticker": "TECHM.NS", "keywords": ["tech mahindra"]},
    "IT: Coforge": {"ticker": "COFORGE.NS", "keywords": ["coforge"]},
    
    # 7. Metals & Mining
    "Metal: Tata Steel": {"ticker": "TATASTEEL.NS", "keywords": ["tata steel"]},
    "Metal: Hindalco": {"ticker": "HINDALCO.NS", "keywords": ["hindalco"]},
    "Metal: JSW Steel": {"ticker": "JSWSTEEL.NS", "keywords": ["jsw steel"]},
    "Metal: Jindal Stainless": {"ticker": "JSL.NS", "keywords": ["jindal stainless", "jsl"]},
    "Metal: Vedanta": {"ticker": "VEDL.NS", "keywords": ["vedanta", "vedl"]},
    
    # 8. Banking & Financials
    "Bank: ICICI Bank": {"ticker": "ICICIBANK.NS", "keywords": ["icici bank", "icici"]},
    "Bank: Axis Bank": {"ticker": "AXISBANK.NS", "keywords": ["axis bank"]},
    "Bank: SBI": {"ticker": "SBIN.NS", "keywords": ["state bank of india", "sbi"]},
    "Bank: Bajaj Finance": {"ticker": "BAJFINANCE.NS", "keywords": ["bajaj finance"]},
    "Bank: Chola Investment": {"ticker": "CHOLAFIN.NS", "keywords": ["cholamandalam", "chola"]}
}

def send_telegram_alert(message):
    if "YOUR_BOT_TOKEN" in TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram alert failed: {e}")

@st.cache_data(ttl=300)
def fetch_stock_data(ticker):
    try:
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if 'Close' not in df.columns or 'High' not in df.columns or 'Low' not in df.columns or 'Volume' not in df.columns:
            return None
        
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['Vol_SMA_20'] = df['Volume'].rolling(20).mean()
        
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift(1))
        low_close = np.abs(df['Low'] - df['Close'].shift(1))
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR_14'] = true_range.rolling(14).mean()
        
        df['Buy_Limit'] = df['EMA_20'] - (1.2 * df['ATR_14'])
        df['Sell_Limit'] = df['Buy_Limit'] + (2.5 * df['ATR_14'])
        
        return df.iloc[-1]
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def find_matching_news(keywords, news_items):
    for item in news_items:
        for kw in keywords:
            if kw in item['title']:
                return item['raw_title'], True
    return "No recent breaking news catalyst", False

# --- STREAMLIT WEB UI ---
st.set_page_config(page_title="Quantitative Swing Trading Alpha Engine", layout="wide")
st.title("⚡ Quantitative Multi-Sector Swing Trading Dashboard")

# Check Nifty Macro Regime
is_bullish_market = check_market_regime()
if is_bullish_market:
    st.success("🌐 **Market Regime Filter:** Nifty 50 is **BULLISH** (Above 50 EMA). Buy and Sell signals are fully active.")
else:
    st.error("⚠️ **Market Regime Filter:** Nifty 50 is **BEARISH** (Below 50 EMA). New BUY signals are suppressed to protect capital.")

if st.button("🔄 Refresh Market Data & Signals"):
    st.rerun()

live_news = fetch_live_news()
dashboard_data = []

for label, info in WATCHLIST.items():
    ticker = info["ticker"]
    keywords = info["keywords"]
    
    latest = fetch_stock_data(ticker)
    news_headline, has_news = find_matching_news(keywords, live_news)
    
    if latest is None:
        dashboard_data.append({
            "Watchlist Item": label,
            "Ticker": ticker,
            "Status": "DATA FETCH FAILED",
            "Action Trigger": "Error"
        })
        continue
        
    try:
        ltp = float(latest['Close'])
        ema20 = float(latest['EMA_20'])
        atr14 = float(latest['ATR_14'])
        buy_limit = float(latest['Buy_Limit'])
        sell_limit = float(latest['Sell_Limit'])
        volume = float(latest['Volume'])
        vol_sma20 = float(latest['Vol_SMA_20'])
        
        distance_from_ema = ((ltp - ema20) / ema20) * 100
        volume_confirmed = volume > vol_sma20
        
        # Position Sizing Calculation (Risk-based sizing for ₹7,500 max loss)
        risk_per_share = 1.2 * atr14
        suggested_qty = int(MAX_RISK_PER_TRADE / risk_per_share) if risk_per_share > 0 else 0
        allocated_capital = min(125000, suggested_qty * ltp) # Capped at ₹1.25L tranche
        
        # --- QUANTITATIVE DECISION ENGINE ---
        if is_bullish_market and ltp <= buy_limit * 1.01 and volume_confirmed:
            status = "STRONG BUY"
            if has_news:
                action_trigger = "🟢 BUY (Regime + Volume + News)"
                send_telegram_alert(f"🚨 *STRONG BUY*: {ticker} ({label}) at ₹{ltp:.2f}!\nQty: {suggested_qty} shares\nNews: {news_headline}")
            else:
                action_trigger = "🟢 BUY (Regime + Volume Action)"
                send_telegram_alert(f"🚨 *STRONG BUY*: {ticker} ({label}) hit buy zone at ₹{ltp:.2f}!\nQty: {suggested_qty} shares")
        elif distance_from_ema > 8.0 or ltp >= sell_limit * 0.995:
            status = "STRONG SELL"
            if has_news:
                action_trigger = "🔴 SELL (Target / News Overextension)"
                send_telegram_alert(f"🚨 *STRONG SELL*: {ticker} ({label}) reached profit target/overextended at ₹{ltp:.2f}!")
            else:
                action_trigger = "🔴 SELL (Target / Price Overextended)"
                send_telegram_alert(f"🚨 *STRONG SELL*: {ticker} ({label}) hit sell limit at ₹{ltp:.2f}!")
        else:
            status = "HOLD / WATCH"
            action_trigger = "🔵 WAITING FOR SETUP" if not volume_confirmed else "⚪ MONITORING"
            
        dashboard_data.append({
            "Watchlist Item": label,
            "Ticker": ticker,
            "Status": status,
            "Action Trigger": action_trigger,
            "Rec. Qty": suggested_qty,
            "Tranche (₹)": round(allocated_capital, 0),
            "LTP (₹)": round(ltp, 2),
            "Buy Limit (₹)": round(buy_limit, 2),
            "Sell Target (₹)": round(sell_limit, 2),
            "Portal News Catalyst": news_headline
        })
    except Exception as e:
        dashboard_data.append({"Watchlist Item": label, "Ticker": ticker, "Status": "ERROR", "Action Trigger": str(e)})

df_display = pd.DataFrame(dashboard_data)
st.dataframe(df_display, width='stretch')

st.markdown("---")
st.markdown("### 💡 Quantitative Risk & Position Sizing Rules (₹5L Capital)")
st.markdown("- **Max Capital Per Tranche:** ₹1,25,000 (Split across 4 tranches max).")
st.markdown("- **Max Risk Per Trade:** 1.5% of total capital (₹7,500) enforced via ATR volatility sizing.")
st.markdown("- **Macro Protection:** If Nifty 50 drops below its 50 EMA, all automated buy alerts freeze automatically.")