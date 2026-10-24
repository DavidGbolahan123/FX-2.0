# MacroEdge FX — standalone prototype

A Streamlit web dashboard for macro-fundamental + technical FX analysis. COT data is intentionally excluded.

## Run locally

1. Install Python 3.10+.
2. Unzip the project.
3. In a terminal, enter the project folder.
4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Start the dashboard:

   ```bash
   streamlit run app.py
   ```

It should open in your browser at the local URL shown by Streamlit.

## Price data modes

- **Yahoo Finance:** attempts to retrieve FX history via `yfinance`. Availability and intraday coverage can vary; validate with your broker.
- **Upload OHLC CSV:** required columns are `Date, Open, High, Low, Close`; `Volume` is optional.
- **Built-in demo data:** synthetic prices only, for testing the interface. Never use demo data to trade.

## Current features

- Major FX pairs and selected crosses
- Macro scorecard with relative base/quote assessment
- Technical indicators: EMA20/50/200, RSI, MACD, ATR and 20-bar swing break
- Transparent separate and combined scores
- News/event risk override
- Chart and illustrative ATR trade plan
- Simple technical-only historical backtest with downloadable trade list

## Important limitations

This is an MVP, not a production-ready trading system. The macro scorecard is manually entered and should be supported by official releases and central-bank statements. Automated economic-calendar ingestion, source citations, historical macro snapshots, persistent storage, multi-timeframe structure analysis and realistic execution modelling are not yet implemented. The backtest is a simple prototype and does not guarantee future performance. Confirm price feeds, timezone, spread, slippage and release data before use.

## Suggested next development phase

1. Integrate a licensed economic calendar with actual/consensus/previous values and release timestamps.
2. Store timestamped macro snapshots and official-source URLs.
3. Add walk-forward tests, spread/slippage/commission and risk-based sizing.
4. Add multi-timeframe technical structure and pair watchlists.
5. Deploy to a secured cloud host with authentication and persistent storage.


## Use it on your iPhone

The dashboard layout is responsive for mobile browsers. To use it like an app:

1. Deploy the project to a hosting service that can run Streamlit (for example, Streamlit Community Cloud from a GitHub repository).
2. Open the deployed HTTPS address in **Safari** on your iPhone.
3. Tap **Share** → **Add to Home Screen**.
4. Name it **MacroEdge FX** and tap **Add**.

This creates a Home Screen shortcut to the web app. It is not a native App Store app, and the dashboard needs an internet connection for live data and hosted access.

## Deploying to Streamlit Community Cloud

1. Create a GitHub repository and upload `app.py`, `requirements.txt`, and `README.md`.
2. Sign in to Streamlit Community Cloud and create an app from that repository.
3. Set the main file path to `app.py` and deploy.
4. Open the generated HTTPS URL on your iPhone and use the steps above.

Do not store broker passwords, API secrets, or other credentials directly in the source code.
