import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timezone

st.set_page_config(page_title="MacroEdge FX", page_icon="📈", layout="wide")

PAIRS = {
    "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "AUD/USD": "AUDUSD=X",
    "NZD/USD": "NZDUSD=X", "USD/JPY": "JPY=X", "USD/CHF": "CHF=X",
    "USD/CAD": "CAD=X", "EUR/GBP": "EURGBP=X", "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X", "AUD/JPY": "AUDJPY=X", "EUR/AUD": "EURAUD=X",
    "GBP/AUD": "GBPAUD=X", "EUR/CHF": "EURCHF=X", "GBP/CHF": "GBPCHF=X",
    "AUD/NZD": "AUDNZD=X", "CAD/JPY": "CADJPY=X", "NZD/JPY": "NZDJPY=X",
}

st.title("📈 MacroEdge FX")
st.caption("Macro-fundamental + technical FX research dashboard • COT excluded by design")


# Mobile-first layout refinements
st.markdown("""
<style>
/* Wider content on small screens, compact cards, readable touch targets */
.block-container {
    padding-top: 1.1rem !important;
    padding-bottom: 5rem !important;
    padding-left: clamp(0.7rem, 3vw, 2rem) !important;
    padding-right: clamp(0.7rem, 3vw, 2rem) !important;
    max-width: 1200px;
}
h1 { font-size: clamp(1.65rem, 5vw, 2.35rem) !important; }
h2 { font-size: clamp(1.25rem, 4vw, 1.75rem) !important; }
h3 { font-size: clamp(1.05rem, 3.5vw, 1.35rem) !important; }
[data-testid="stMetric"] {
    background: rgba(128, 128, 128, 0.08);
    border: 1px solid rgba(128, 128, 128, 0.18);
    padding: 0.7rem 0.8rem;
    border-radius: 0.8rem;
}
[data-testid="stMetricValue"] { font-size: clamp(1.15rem, 4vw, 1.8rem) !important; }
.stButton button, .stDownloadButton button {
    min-height: 2.75rem;
    border-radius: 0.7rem;
    width: 100%;
}
div[data-testid="stSelectbox"] label,
div[data-testid="stSlider"] label,
div[data-testid="stRadio"] label { font-weight: 600; }
[data-testid="stDataFrame"] { width: 100%; }
@media (max-width: 768px) {
    .block-container { padding-top: 0.7rem !important; }
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 0.65rem !important;
    }
    [data-testid="column"] {
        min-width: calc(50% - 0.4rem) !important;
        flex: 1 1 calc(50% - 0.4rem) !important;
    }
    [data-testid="stMetric"] { padding: 0.55rem; }
    [data-testid="stMetricLabel"] { font-size: 0.78rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.1rem !important; }
    [data-testid="stPlotlyChart"] { overflow-x: auto; }
    [data-testid="stSidebar"] { min-width: 0 !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 0.25rem; }
    .stTabs [data-baseweb="tab"] { padding: 0.45rem 0.6rem; }
}
</style>
""", unsafe_allow_html=True)

st.info("Research prototype: market data availability depends on the configured provider. Verify prices and economic releases before trading. Signals are analytical scenarios, not guaranteed outcomes.")

with st.sidebar:
    st.header("Workspace")
    selected_pair = st.selectbox("Currency pair", list(PAIRS.keys()), index=0)
    timeframe = st.selectbox("Technical timeframe", ["1d", "1wk", "1h", "4h"], index=0)
    period = st.selectbox("Price history", ["3mo", "6mo", "1y", "2y", "5y"], index=2)
    data_mode = st.radio("Price source", ["Yahoo Finance (when available)", "Upload OHLC CSV", "Built-in demo data"], index=0)
    uploaded = st.file_uploader("Upload OHLC CSV", type=["csv"]) if data_mode == "Upload OHLC CSV" else None
    st.divider()
    st.caption("CSV columns required: Date, Open, High, Low, Close. Volume is optional.")

@st.cache_data(ttl=900, show_spinner=False)
def get_yahoo_data(ticker, period, interval):
    import yfinance as yf
    data = yf.download(ticker, period=period, interval=interval, auto_adjust=False, progress=False)
    if data is None or data.empty:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data = data.reset_index()
    if "Datetime" in data.columns:
        data = data.rename(columns={"Datetime": "Date"})
    return data

def demo_data():
    # Explicitly synthetic data for UI demonstration only.
    rng = np.random.default_rng(23)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=350, freq="B")
    close = 1.08 + np.cumsum(rng.normal(0, 0.003, len(dates)))
    opn = np.r_[close[0], close[:-1]] + rng.normal(0, 0.001, len(dates))
    high = np.maximum(opn, close) + rng.uniform(0.0002, 0.002, len(dates))
    low = np.minimum(opn, close) - rng.uniform(0.0002, 0.002, len(dates))
    return pd.DataFrame({"Date": dates, "Open": opn, "High": high, "Low": low, "Close": close, "Volume": 0})

def normalize_ohlc(df):
    df = df.copy()
    df.columns = [str(c).strip().title() for c in df.columns]
    if "Datetime" in df.columns and "Date" not in df.columns:
        df = df.rename(columns={"Datetime": "Date"})
    required = ["Date", "Open", "High", "Low", "Close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for c in ["Open", "High", "Low", "Close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=required).sort_values("Date").drop_duplicates("Date")
    return df.reset_index(drop=True)

def add_indicators(df):
    d = df.copy()
    d["EMA20"] = d["Close"].ewm(span=20, adjust=False).mean()
    d["EMA50"] = d["Close"].ewm(span=50, adjust=False).mean()
    d["EMA200"] = d["Close"].ewm(span=200, adjust=False).mean()
    delta = d["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    d["RSI"] = 100 - (100 / (1 + rs))
    ema12 = d["Close"].ewm(span=12, adjust=False).mean()
    ema26 = d["Close"].ewm(span=26, adjust=False).mean()
    d["MACD"] = ema12 - ema26
    d["MACD_Signal"] = d["MACD"].ewm(span=9, adjust=False).mean()
    prev_close = d["Close"].shift(1)
    tr = pd.concat([(d["High"]-d["Low"]), (d["High"]-prev_close).abs(), (d["Low"]-prev_close).abs()], axis=1).max(axis=1)
    d["ATR"] = tr.rolling(14).mean()
    d["SwingHigh"] = d["High"].rolling(20).max().shift(1)
    d["SwingLow"] = d["Low"].rolling(20).min().shift(1)
    return d

def technical_score(row, prev=None):
    score, reasons = 0, []
    if pd.notna(row.get("EMA20")) and pd.notna(row.get("EMA50")):
        if row["Close"] > row["EMA20"] > row["EMA50"]:
            score += 25; reasons.append("Price above EMA20 and EMA50: bullish trend alignment.")
        elif row["Close"] < row["EMA20"] < row["EMA50"]:
            score -= 25; reasons.append("Price below EMA20 and EMA50: bearish trend alignment.")
        else:
            reasons.append("EMA trend is mixed.")
    if pd.notna(row.get("EMA200")):
        if row["Close"] > row["EMA200"]:
            score += 15; reasons.append("Price above EMA200.")
        else:
            score -= 15; reasons.append("Price below EMA200.")
    if pd.notna(row.get("RSI")):
        if 52 <= row["RSI"] <= 68:
            score += 15; reasons.append("RSI has bullish momentum without being deeply overbought.")
        elif 32 <= row["RSI"] <= 48:
            score -= 15; reasons.append("RSI has bearish momentum without being deeply oversold.")
        elif row["RSI"] > 70:
            score -= 5; reasons.append("RSI is overbought; chase risk is elevated.")
        elif row["RSI"] < 30:
            score += 5; reasons.append("RSI is oversold; downside may be extended.")
    if pd.notna(row.get("MACD")) and pd.notna(row.get("MACD_Signal")):
        if row["MACD"] > row["MACD_Signal"]:
            score += 15; reasons.append("MACD is above its signal line.")
        else:
            score -= 15; reasons.append("MACD is below its signal line.")
    if pd.notna(row.get("SwingHigh")) and row["Close"] > row["SwingHigh"]:
        score += 20; reasons.append("Close broke above the prior 20-bar swing high.")
    elif pd.notna(row.get("SwingLow")) and row["Close"] < row["SwingLow"]:
        score -= 20; reasons.append("Close broke below the prior 20-bar swing low.")
    return int(np.clip(score, -100, 100)), reasons

def score_label(score):
    if score >= 40: return "Bullish"
    if score <= -40: return "Bearish"
    return "Mixed / wait"

# Load data
data = pd.DataFrame()
data_warning = ""
try:
    if data_mode == "Upload OHLC CSV":
        if uploaded is not None:
            data = normalize_ohlc(pd.read_csv(uploaded))
        else:
            st.warning("Upload an OHLC CSV to continue, or switch to another price source.")
    elif data_mode == "Built-in demo data":
        data = normalize_ohlc(demo_data())
        data_warning = "Synthetic demo prices are being used. Do not treat the output as a live signal."
    else:
        try:
            interval_map = {"1d":"1d", "1wk":"1wk", "1h":"1h", "4h":"1h"}
            raw = get_yahoo_data(PAIRS[selected_pair], period, interval_map[timeframe])
            if timeframe == "4h" and not raw.empty:
                raw = raw.set_index("Date").resample("4h").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna().reset_index()
            data = normalize_ohlc(raw) if not raw.empty else pd.DataFrame()
            if data.empty:
                data_warning = "The selected data provider returned no data for this pair/timeframe. Try a different pair or upload OHLC data."
        except Exception as e:
            data_warning = f"Market data could not be loaded: {e}. Check internet/provider availability or upload OHLC data."
except Exception as e:
    st.error(f"Could not process price data: {e}")

if data_warning:
    st.warning(data_warning)

# Macro inputs are intentionally transparent and editable; no hidden/fabricated macro feed.
st.subheader("1. Fundamental assessment")
st.caption("Enter the latest verified macro evidence for each currency. This prototype does not pretend manually entered scores are live economic data.")
currencies = list(dict.fromkeys([selected_pair[:3], selected_pair[-3:]]))
c1, c2 = st.columns(2)
with c1:
    st.markdown(f"**{currencies[0]} — base currency**")
    base_policy = st.slider(f"{currencies[0]} policy/rate outlook", -2, 2, 0, help="-2 = strongly dovish/weakening; +2 = strongly hawkish/strengthening")
    base_inflation = st.slider(f"{currencies[0]} inflation surprise/trend", -2, 2, 0, help="Score the latest verified trend/surprise, not simply whether inflation is high.")
    base_growth = st.slider(f"{currencies[0]} growth/employment momentum", -2, 2, 0)
    base_risk = st.slider(f"{currencies[0]} domestic risk / terms of trade", -2, 2, 0)
with c2:
    st.markdown(f"**{currencies[1]} — quote currency**")
    quote_policy = st.slider(f"{currencies[1]} policy/rate outlook", -2, 2, 0)
    quote_inflation = st.slider(f"{currencies[1]} inflation surprise/trend", -2, 2, 0)
    quote_growth = st.slider(f"{currencies[1]} growth/employment momentum", -2, 2, 0)
    quote_risk = st.slider(f"{currencies[1]} domestic risk / terms of trade", -2, 2, 0)
base_score = base_policy*12.5 + base_inflation*7.5 + base_growth*7.5 + base_risk*5
quote_score = quote_policy*12.5 + quote_inflation*7.5 + quote_growth*7.5 + quote_risk*5
macro_score = int(np.clip(base_score - quote_score, -100, 100))
with st.expander("Macro evidence log — record sources and upcoming catalysts"):
    evidence = st.text_area("What official releases or central-bank statements support your scores?", placeholder="Example: central-bank statement dated…, CPI actual vs consensus…, payrolls…, GDP/PMI…")
    event_notes = st.text_area("Upcoming high-impact events and release times (include timezone)", placeholder="Example: CPI on YYYY-MM-DD at HH:MM UTC; central-bank decision…")
    event_risk = st.selectbox("Event risk for this pair", ["Low", "Moderate", "High", "Very high"], index=1)
    macro_confidence = st.select_slider("Confidence in macro evidence quality", options=["Low", "Medium", "High"], value="Medium")
st.caption("Macro score weights: policy/rate outlook 25%, inflation 15%, growth/employment 15%, domestic risk/terms of trade 10%, applied as a relative base-minus-quote score. Remaining scoring capacity is reserved for future source-verified expectations and revisions. Scores are analyst inputs in this MVP, not an automated news feed.")

# Dashboard
st.subheader("2. Signal dashboard")
if not data.empty and len(data) >= 30:
    data = add_indicators(data)
    last = data.iloc[-1]
    t_score, t_reasons = technical_score(last)
    combined = int(np.clip(0.55*macro_score + 0.45*t_score, -100, 100))
    label = score_label(combined)
    if event_risk in ["High", "Very high"]:
        label = "Wait — event risk"
    cols = st.columns(5)
    cols[0].metric("Latest close", f"{last['Close']:.5f}")
    cols[1].metric("Macro score", f"{macro_score:+d}/100")
    cols[2].metric("Technical score", f"{t_score:+d}/100")
    cols[3].metric("Combined score", f"{combined:+d}/100")
    cols[4].metric("Signal bias", label)
    st.caption(f"Combined score = 55% macro + 45% technical. Scores are directional evidence, not statistical probabilities.")
    # chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=data["Date"], open=data["Open"], high=data["High"], low=data["Low"], close=data["Close"], name="Price"))
    for col, color in [("EMA20","#F5A623"),("EMA50","#4F8EF7"),("EMA200","#B56BE8")]:
        if data[col].notna().any():
            fig.add_trace(go.Scatter(x=data["Date"], y=data[col], name=col, line=dict(width=1.4, color=color)))
    fig.update_layout(height=520, xaxis_rangeslider_visible=False, margin=dict(l=10,r=10,t=25,b=10), legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Technical evidence")
        for reason in t_reasons:
            st.write("• " + reason)
    with c2:
        st.markdown("#### Fundamental interpretation")
        st.write(f"Relative macro score for {selected_pair}: **{macro_score:+d}/100**.")
        st.write("Base-currency score:", f"{base_score:+.1f}")
        st.write("Quote-currency score:", f"{quote_score:+.1f}")
        st.write("Evidence log:", evidence or "Not supplied yet.")
        st.write("Macro evidence confidence:", macro_confidence)
        st.write("Event risk:", event_risk)
        st.write("Upcoming catalysts:", event_notes or "Not supplied yet.")
    # trade plan using ATR, no invented entry if data not enough
    st.markdown("#### Illustrative trade plan")
    if pd.notna(last["ATR"]) and last["ATR"] > 0 and label in ["Bullish", "Bearish"]:
        direction = 1 if label == "Bullish" else -1
        entry = float(last["Close"])
        stop = entry - direction*1.5*float(last["ATR"])
        target1 = entry + direction*1.5*float(last["ATR"])
        target2 = entry + direction*3.0*float(last["ATR"])
        st.write(f"Reference entry (last close): `{entry:.5f}` · Stop: `{stop:.5f}` · Target 1: `{target1:.5f}` · Target 2: `{target2:.5f}`")
        st.caption("Illustrative ATR-based levels only. Confirm spread, session liquidity, structure, and news timing before any trade.")
    else:
        st.write("No actionable plan: the score is mixed or event risk is too high. Wait for better alignment.")
else:
    st.info("Load at least 30 OHLC rows to calculate indicators and a technical score.")

# Backtest
st.subheader("3. Historical strategy test")
st.caption("Simple educational backtest: enter at next bar's open after a score threshold; exit when signal reverses or after a fixed holding period. It is not a realistic execution simulator and excludes spread/slippage unless adjusted below.")
if not data.empty and len(data) >= 80:
    b1, b2, b3 = st.columns(3)
    threshold = b1.slider("Directional score threshold", 20, 80, 40, step=5)
    hold_bars = b2.slider("Maximum holding bars", 3, 30, 10)
    cost_bps = b3.number_input("Estimated round-trip costs (basis points)", min_value=0.0, max_value=100.0, value=2.0, step=0.5)
    bt = data.copy()
    # Only technical component is historically reproducible; current macro inputs are not backfilled.
    bt["TechScore"] = 0
    for i in range(len(bt)):
        s, _ = technical_score(bt.iloc[i])
        bt.loc[bt.index[i], "TechScore"] = s
    bt["Signal"] = np.where(bt["TechScore"] >= threshold, 1, np.where(bt["TechScore"] <= -threshold, -1, 0))
    trades = []
    i = 0
    while i < len(bt)-1:
        sig = int(bt.iloc[i]["Signal"])
        if sig == 0:
            i += 1; continue
        entry_i = i + 1
        exit_i = min(entry_i + hold_bars, len(bt)-1)
        # Exit early if opposing signal appears; otherwise fixed max hold.
        for j in range(entry_i+1, min(entry_i+hold_bars+1, len(bt))):
            if int(bt.iloc[j]["Signal"]) == -sig:
                exit_i = j
                break
        entry_price = float(bt.iloc[entry_i]["Open"])
        exit_price = float(bt.iloc[exit_i]["Close"])
        gross = sig*(exit_price/entry_price - 1)
        net = gross - cost_bps/10000
        trades.append({"Entry date": bt.iloc[entry_i]["Date"], "Exit date": bt.iloc[exit_i]["Date"], "Side": "Long" if sig==1 else "Short", "Entry": entry_price, "Exit": exit_price, "Net return %": net*100})
        i = exit_i + 1
    if trades:
        tr = pd.DataFrame(trades)
        tr["Equity"] = (1 + tr["Net return %"]/100).cumprod()
        total = (tr["Equity"].iloc[-1]-1)*100
        win = (tr["Net return %"] > 0).mean()*100
        avg = tr["Net return %"].mean()
        peak = tr["Equity"].cummax()
        dd = ((tr["Equity"]/peak)-1).min()*100
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Trades", f"{len(tr)}")
        m2.metric("Win rate", f"{win:.1f}%")
        m3.metric("Cumulative return", f"{total:.2f}%")
        m4.metric("Max drawdown", f"{dd:.2f}%")
        st.write(f"Average net return per trade: **{avg:.3f}%**")
        st.dataframe(tr.tail(100), use_container_width=True, hide_index=True)
        st.download_button("Download backtest trades CSV", tr.to_csv(index=False).encode("utf-8"), file_name=f"{selected_pair.replace('/','')}_backtest.csv", mime="text/csv")
    else:
        st.warning("No trades met the selected threshold in this history.")
else:
    st.info("Backtesting requires at least 80 OHLC rows.")

with st.expander("Methodology, limitations and next steps"):
    st.markdown("""
    **Included:** editable macro scorecard, technical indicators (EMA20/50/200, RSI, MACD, ATR), swing-break check, event-risk override, OHLC chart, illustrative ATR trade plan and a simple historical technical backtest.

    **Not included yet:** verified live economic-calendar feed, automated central-bank/news interpretation, broker-grade streaming quotes, walk-forward optimization, multi-timeframe structure detection, spread-aware execution simulation, and persistent database/watchlists.

    **Important:** the macro score is entered by the analyst and must be backed by official sources. The backtest tests the technical rules only because historical macro scores are not currently stored. Do not interpret the combined score as a win probability. Yahoo Finance symbols and intraday history can be incomplete or delayed. Validate all data against a broker or trusted provider.
    """)
st.caption("MacroEdge FX • No COT data is used.")
