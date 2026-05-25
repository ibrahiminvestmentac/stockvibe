import os
import re
import requests
import xml.etree.ElementTree as ET
import urllib.parse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Preferred List of major Indian tickers
PREFERRED_TICKERS = {
    "TCS": "TCS.NS",
    "RELIANCE": "RELIANCE.NS",
    "COAL INDIA": "COALINDIA.NS",
    "COALINDIA": "COALINDIA.NS",
    "INFY": "INFY.NS",
    "INFOSYS": "INFY.NS",
    "HDFC BANK": "HDFCBANK.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICI BANK": "ICICIBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "SBI": "SBIN.NS",
    "SBIN": "SBIN.NS",
    "STATE BANK OF INDIA": "SBIN.NS",
    "BHARTI AIRTEL": "BHARTIARTL.NS",
    "AIRTEL": "BHARTIARTL.NS",
    "L&T": "LT.NS",
    "LARSEN": "LT.NS",
    "ITC": "ITC.NS",
    "HINDALCO": "HINDALCO.NS",
    "WIPRO": "WIPRO.NS",
    "TATA MOTORS": "TATAMOTORS.NS",
    "TATA STEEL": "TATASTEEL.NS",
    "MARUTI": "MARUTI.NS",
    "ADANI ENTERPRISES": "ADANIENT.NS",
    "ADANI": "ADANIENT.NS",
    "KOTAK BANK": "KOTAKBANK.NS",
    "KOTAK": "KOTAKBANK.NS",
    "AXIS BANK": "AXISBANK.NS",
    "AXIS": "AXISBANK.NS",
    "HINDUNILVR": "HINDUNILVR.NS",
    "HINDUSTAN UNILEVER": "HINDUNILVR.NS",
    "ASIAN PAINTS": "ASIANPAINT.NS",
    "ASIANPAINT": "ASIANPAINT.NS"
}

# Lexicon for financial news sentiment analysis
SENTIMENT_LEXICON = {
    # Strong Positive (2.0 to 3.0)
    "surge": 2.5, "surges": 2.5, "surged": 2.5, "surging": 2.5,
    "profit": 2.0, "profits": 2.0, "profitable": 2.0,
    "bullish": 2.2, "stellar": 2.5, "soar": 2.5, "soars": 2.5, "soared": 2.5, "soaring": 2.5,
    "outperform": 2.0, "rally": 2.0, "rallies": 2.0, "rallied": 2.0,
    "beat": 1.5, "beats": 1.5, "beaten": 1.5, "beating": 1.5,
    "growth": 1.8, "grow": 1.5, "grows": 1.5, "growing": 1.5, "grown": 1.5,
    "boost": 1.8, "boosts": 1.8, "boosted": 1.8,
    "record": 1.7, "records": 1.7, "blockbuster": 2.5,
    
    # Moderate Positive (1.0 to 1.5)
    "gain": 1.5, "gains": 1.5, "gained": 1.5, "gaining": 1.5,
    "upgrade": 2.0, "upgraded": 2.0, "upgrades": 2.0,
    "rise": 1.2, "rises": 1.2, "rising": 1.2, "rose": 1.2,
    "high": 1.0, "higher": 1.2, "highest": 1.5,
    "positive": 1.5, "buy": 1.5, "buys": 1.5, "buying": 1.5,
    "win": 1.5, "wins": 1.5, "won": 1.5,
    "expand": 1.5, "expansion": 1.5, "expands": 1.5,
    "dividend": 1.2, "dividends": 1.2,
    "strong": 1.5, "strength": 1.5, "strengthens": 1.5,
    "optimistic": 1.8, "optimism": 1.8,
    
    # Strong Negative (-2.0 to -3.0)
    "crash": -3.0, "crashed": -3.0, "crashing": -3.0, "crashes": -3.0,
    "loss": -2.0, "losses": -2.0, "lose": -1.8, "loses": -1.8, "losing": -1.8, "lost": -1.8,
    "bearish": -2.2, "slump": -2.5, "slumps": -2.5, "slumped": -2.5, "slumping": -2.5,
    "plunge": -2.5, "plunges": -2.5, "plunged": -2.5, "plunging": -2.5,
    "tumble": -2.0, "tumbles": -2.0, "tumbled": -2.0, "tumbling": -2.0,
    "crisis": -2.5, "scam": -3.0, "fraud": -3.0, "investigation": -1.5, "probe": -1.5,
    "downgrade": -2.0, "downgraded": -2.0, "downgrades": -2.0,
    
    # Moderate Negative (-1.0 to -1.5)
    "decline": -1.5, "declines": -1.5, "declined": -1.5, "declining": -1.5,
    "drop": -1.2, "drops": -1.2, "dropped": -1.2, "dropping": -1.2,
    "fall": -1.2, "falls": -1.2, "fell": -1.2, "falling": -1.2,
    "miss": -1.5, "misses": -1.5, "missed": -1.5, "missing": -1.5,
    "debt": -1.2, "debts": -1.2, "deficit": -1.5,
    "negative": -1.5, "sell": -1.5, "sells": -1.5, "selling": -1.5,
    "warning": -1.8, "warnings": -1.8, "warns": -1.5, "warned": -1.5,
    "risk": -1.2, "risks": -1.2, "risky": -1.5,
    "weak": -1.5, "weakness": -1.5, "weaker": -1.5,
    "inflation": -1.0, "pressure": -1.0, "pressures": -1.0, "pressured": -1.2
}

def call_llm(system_prompt, user_prompt, temperature=0.1):
    """
    Executes an LLM call using either Groq or Gemini API keys.
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    # Try Groq first
    if groq_key:
        try:
            client = Groq(api_key=groq_key)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"[stock_agent] Groq API Call Failed: {e}. Trying Gemini...")

    # Try Gemini next via HTTP POST requests
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={gemini_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": f"System Instruction: {system_prompt}\n\nUser Input: {user_prompt}"}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": temperature
                }
            }
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data['candidates'][0]['content']['parts'][0]['text'].strip()
            else:
                print(f"[stock_agent] Gemini API HTTP Error {res.status_code}: {res.text}")
        except Exception as e:
            print(f"[stock_agent] Gemini API HTTP exception: {e}")

    # Fallback response if neither works
    return "NONE"

def discover_ticker(message):
    """
    Parses user message for stock tickers.
    1. Explicit check for .NS or .BO
    2. Maps keywords to hardcoded Indian list
    3. Classification LLM call
    """
    # 1. Regex check for .NS or .BO
    explicit_match = re.search(r'\b([A-Z0-9_-]+)\.(NS|BO)\b', message.upper())
    if explicit_match:
        return explicit_match.group(0)

    # 2. Preferred List mapping check (word boundaries)
    clean_message = re.sub(r'[^\w\s]', ' ', message.upper())
    tokens = clean_message.split()
    for token in tokens:
        if token in PREFERRED_TICKERS:
            return PREFERRED_TICKERS[token]
            
    # Check multi-word keys from Preferred List
    for key, ticker in PREFERRED_TICKERS.items():
        if key in clean_message:
            return ticker

    # 3. LLM-based Ticker Discovery
    system_prompt = (
        "You are an expert financial routing assistant for a premium stock terminal. "
        "Analyze the user's input. If they are requesting details, analysis, price, or "
        "sentiment of a specific stock, company, or asset, determine the primary stock ticker symbol. "
        "For Indian companies, default to appending '.NS' (NSE format), e.g. 'RELIANCE' -> 'RELIANCE.NS'. "
        "For US companies, return the standard ticker, e.g. 'Apple' -> 'AAPL'. "
        "Return ONLY the ticker symbol in uppercase, with no punctuation or extra words. "
        "If the user is greeting you (e.g., 'hello', 'hi'), asking general questions, or discussing "
        "topics unrelated to checking a specific stock/company, return ONLY the word 'NONE'."
    )
    user_prompt = f"Identify ticker from: \"{message}\""
    
    ticker_val = call_llm(system_prompt, user_prompt, temperature=0.0)
    ticker_val = ticker_val.strip().upper().replace('"', '').replace("'", "")
    
    # Strip any extra text the LLM might have returned
    ticker_match = re.search(r'\b([A-Z0-9\.-]+)\b', ticker_val)
    if ticker_match:
        ticker_val = ticker_match.group(1)
        
    if ticker_val == "NONE" or len(ticker_val) > 12:
        return "NONE"
        
    return ticker_val

def calculate_rsi(prices, period=14):
    """
    Calculates the 14-day Relative Strength Index.
    """
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    # Wilder's smoothing
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    
    rs = avg_gain / (avg_loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices):
    """
    Calculates MACD Line, Signal Line and crossover signals.
    """
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    
    crossover = "NEUTRAL"
    if len(macd_line) > 1:
        prev_m, prev_s = macd_line.iloc[-2], signal_line.iloc[-2]
        curr_m, curr_s = macd_line.iloc[-1], signal_line.iloc[-1]
        if prev_m <= prev_s and curr_m > curr_s:
            crossover = "BULLISH CROSS"
        elif prev_m >= prev_s and curr_m < curr_s:
            crossover = "BEARISH CROSS"
            
    return macd_line, signal_line, crossover

def calculate_bollinger_bands(prices, period=20):
    """
    Calculates 20-day SMA, Upper/Lower bands, and percentage band width.
    """
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = sma + (std * 2)
    lower = sma - (std * 2)
    
    bandwidth = (upper - lower) / (sma + 1e-9)
    pct_b = (prices - lower) / (upper - lower + 1e-9)
    
    return upper, lower, bandwidth, pct_b

def calculate_fibonacci(df):
    """
    Calculates Fibonacci Retracement levels (0.236, 0.382, 0.500, 0.618)
    based on the High-Low range of the last 6 months (126 trading days).
    """
    # 6 months ~ 126 trading days
    lookback = min(126, len(df))
    sub_df = df.iloc[-lookback:]
    high_val = sub_df['High'].max()
    low_val = sub_df['Low'].min()
    diff = high_val - low_val
    
    return {
        "high": float(high_val),
        "low": float(low_val),
        "fib_236": float(high_val - 0.236 * diff),
        "fib_382": float(high_val - 0.382 * diff),
        "fib_500": float(high_val - 0.500 * diff),
        "fib_618": float(high_val - 0.618 * diff)
    }

def calculate_moving_averages(df):
    """
    Calculates 50-day and 200-day EMAs.
    Returns: ema50, ema200, cross_signal
    """
    ema50 = df['Close'].ewm(span=50, adjust=False).mean()
    ema200 = df['Close'].ewm(span=200, adjust=False).mean()
    
    current_ema50 = float(ema50.iloc[-1])
    current_ema200 = float(ema200.iloc[-1])
    
    cross_signal = "GOLDEN CROSS" if current_ema50 > current_ema200 else "DEATH CROSS"
    return current_ema50, current_ema200, cross_signal

def calculate_adx(df, period=14):
    """
    Calculates the 14-day Average Directional Index (ADX).
    Identifies if price regime is TRENDING (ADX > 25, +DI > -DI), 
    DOWNTRENDING (ADX > 25, -DI > +DI), or RANGING/NEUTRAL.
    """
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1/period, adjust=False).mean() / (atr + 1e-9)
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1/period, adjust=False).mean() / (atr + 1e-9)
    
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    
    adx_val = float(adx.iloc[-1])
    plus_di_val = float(plus_di.iloc[-1])
    minus_di_val = float(minus_di.iloc[-1])
    
    if adx_val > 25:
        if plus_di_val > minus_di_val:
            regime = "TRENDING BULLISH"
        else:
            regime = "TRENDING BEARISH"
    else:
        regime = "RANGING/NEUTRAL"
        
    return adx_val, plus_di_val, minus_di_val, regime

def check_breakout(df):
    """
    Check if the current close exceeds the previous 25-day high (Breakout).
    """
    if len(df) < 27:
        return False
    prev_25_high = df['High'].iloc[-26:-1].max()
    current_close = df['Close'].iloc[-1]
    return bool(current_close > prev_25_high)

def fetch_google_news(query):
    """
    Fetches the latest 12 news headlines via Google News RSS parser.
    """
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}+stock+market&hl=en-IN&gl=IN&ceid=IN:en"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return []
            
        root = ET.fromstring(res.content)
        news_items = []
        
        for item in root.findall('.//item')[:12]:
            title = item.find('title').text if item.find('title') is not None else "No Title"
            link = item.find('link').text if item.find('link') is not None else "#"
            pub_date_raw = item.find('pubDate').text if item.find('pubDate') is not None else ""
            source_el = item.find('source')
            source = source_el.text if source_el is not None else "Google News"
            
            # Format title (remove source string e.g., "Reliance Share Price - Moneycontrol")
            clean_title = title
            if " - " in title:
                clean_title = " - ".join(title.split(" - ")[:-1])
            
            # Simple date parsing/formatting
            pub_date = pub_date_raw
            if pub_date_raw:
                try:
                    dt = datetime.strptime(pub_date_raw, "%a, %d %b %Y %H:%M:%S %Z")
                    pub_date = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pub_date = pub_date_raw
                    
            # Compute individual headline sentiment
            headline_score = analyze_headline_sentiment(clean_title)
            sentiment_cat = "STABLE"
            if headline_score >= 0.5:
                sentiment_cat = "EXCUBERANT"
            elif headline_score >= 0.1:
                sentiment_cat = "POSITIVE"
            elif headline_score <= -0.5:
                sentiment_cat = "PANIC"
            elif headline_score <= -0.1:
                sentiment_cat = "NEGATIVE"
                
            news_items.append({
                "title": clean_title,
                "link": link,
                "pub_date": pub_date,
                "source": source,
                "score": headline_score,
                "sentiment": sentiment_cat
            })
            
        return news_items
    except Exception as e:
        print(f"[stock_agent] Google News scraping failed: {e}")
        return []

def analyze_headline_sentiment(headline):
    """
    Lexicon-based scoring of a single headline.
    Returns normalized score between -1.0 and +1.0.
    """
    clean_text = re.sub(r'[^\w\s]', ' ', headline.lower())
    words = clean_text.split()
    
    score = 0.0
    matches = 0
    
    for word in words:
        if word in SENTIMENT_LEXICON:
            score += SENTIMENT_LEXICON[word]
            matches += 1
            
    # Normalize score
    if matches > 0:
        # Clamp sum between -3.0 and 3.0, and map to -1.0 to 1.0
        normalized = score / (matches * 2.5) # Scale slightly by matching word count
        return max(-1.0, min(1.0, normalized))
    
    return 0.0

def fetch_history_via_chart_api(ticker, session=None):
    """
    Directly queries Yahoo Finance chart JSON API.
    Bypasses standard yfinance crumb rate-limit blocks on servers.
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=2y&interval=1d"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        if session:
            res = session.get(url, headers=headers, timeout=10)
        else:
            res = requests.get(url, headers=headers, timeout=10)
            
        if res.status_code != 200:
            return pd.DataFrame()
            
        data = res.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            return pd.DataFrame()
            
        result_data = result[0]
        timestamps = result_data.get("timestamp", [])
        quote = result_data.get("indicators", {}).get("quote", [{}])[0]
        adjclose = result_data.get("indicators", {}).get("adjclose", [{}])[0].get("adjclose", [])
        
        # Build pandas DataFrame
        dt_index = pd.to_datetime(timestamps, unit="s")
        
        df = pd.DataFrame({
            "Open": quote.get("open", []),
            "High": quote.get("high", []),
            "Low": quote.get("low", []),
            "Close": adjclose if adjclose else quote.get("close", []),
            "Volume": quote.get("volume", [])
        }, index=dt_index)
        
        df = df.dropna(subset=["Close"])
        return df
    except Exception as e:
        print(f"[stock_agent] Chart API fallback failed: {e}")
        return pd.DataFrame()

def run_quantitative_analysis(ticker):
    """
    Fetches stock details from yfinance and calculates technical indicators.
    """
    import yfinance as yf
    
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        stock = yf.Ticker(ticker, session=session)
        
        # 2 years of daily data
        try:
            df = stock.history(period="2y")
        except Exception as hist_err:
            print(f"[stock_agent] Warning: stock.history failed: {hist_err}. Trying direct chart API fallback...")
            df = pd.DataFrame()
            
        if df.empty:
            print("[stock_agent] yfinance history was empty. Trying direct chart API fallback...")
            df = fetch_history_via_chart_api(ticker, session=session)
            
        if df.empty:
            return None
            
        # Standardize columns to case-insensitive
        df.columns = [col.capitalize() for col in df.columns]
        
        # Latest prices
        current_price = float(df['Close'].iloc[-1])
        prev_price = float(df['Close'].iloc[-2]) if len(df) > 1 else current_price
        price_change_pct = float(((current_price - prev_price) / prev_price) * 100)
        
        # Fundamentals info
        try:
            info = stock.info
            if not info:
                info = {}
        except Exception as info_err:
            print(f"[stock_agent] Warning: Failed to fetch stock.info: {info_err}")
            info = {}
        
        # Extract fundamentals
        market_cap = info.get('marketCap', 0)
        pe_ratio = info.get('trailingPE', info.get('forwardPE', 'N/A'))
        roe = info.get('returnOnEquity', 'N/A')
        de_ratio = info.get('debtToEquity', 'N/A')
        dividend_yield = info.get('dividendYield', 0.0)
        
        # Convert values to standard formats
        if roe != 'N/A' and isinstance(roe, (int, float)):
            roe = f"{roe * 100:.2f}%"
        if dividend_yield != 'N/A' and isinstance(dividend_yield, (int, float)):
            if dividend_yield < 0.15:
                dividend_yield = dividend_yield * 100
            dividend_yield = f"{dividend_yield:.2f}%"
        if market_cap and isinstance(market_cap, (int, float)):
            if market_cap >= 1e12:
                market_cap_str = f"₹{market_cap / 1e12:.2f}T"
            elif market_cap >= 1e9:
                market_cap_str = f"₹{market_cap / 1e9:.2f}B"
            elif market_cap >= 1e7:
                market_cap_str = f"₹{market_cap / 1e7:.2f} Cr"
            else:
                market_cap_str = f"₹{market_cap:,.2f}"
        else:
            market_cap_str = "N/A"
            
        # Capitalization Category (Rough Estimate in Indian context or general context)
        cap_val = info.get('marketCap', 0)
        if cap_val >= 200000000000: # 20,000 Crores (Large Cap)
            cap_cat = "Large Cap"
        elif cap_val >= 50000000000: # 5,000 Crores (Mid Cap)
            cap_cat = "Mid Cap"
        elif cap_val > 0:
            cap_cat = "Small Cap"
        else:
            cap_cat = "N/A"
            
        long_name = info.get('longName', info.get('shortName', ticker))
        
        # Calculate Technicals
        rsi_series = calculate_rsi(df['Close'])
        rsi_val = float(rsi_series.iloc[-1])
        
        macd_line, signal_line, macd_cross = calculate_macd(df['Close'])
        macd_val = float(macd_line.iloc[-1])
        macd_sig = float(signal_line.iloc[-1])
        
        upper_b, lower_b, bandwidth, pct_b = calculate_bollinger_bands(df['Close'])
        volatility_width = float(bandwidth.iloc[-1])
        upper_b_val = float(upper_b.iloc[-1])
        lower_b_val = float(lower_b.iloc[-1])
        pct_b_val = float(pct_b.iloc[-1])
        
        fib_levels = calculate_fibonacci(df)
        
        ema50, ema200, ema_cross = calculate_moving_averages(df)
        
        adx_val, plus_di, minus_di, adx_regime = calculate_adx(df)
        
        breakout_status = check_breakout(df)
        breakout_alert = "BREAKOUT DETECTED" if breakout_status else "NO BREAKOUT"
        
        # Risk Management (Volatility Band Width * 0.75 and 1.5)
        stop_loss = float(current_price * (1.0 - (volatility_width * 0.75)))
        take_profit = float(current_price * (1.0 + (volatility_width * 1.5)))
        risk_reward_ratio = "2.0:1 (Volatility Scaled)"
        
        # Fetch News
        news_query = long_name if long_name else ticker
        news_headlines = fetch_google_news(news_query)
        
        # Calculate News Sentiment Average
        if news_headlines:
            avg_sentiment_score = sum(h['score'] for h in news_headlines) / len(news_headlines)
        else:
            avg_sentiment_score = 0.0
            
        sentiment_category = "STABLE"
        if avg_sentiment_score >= 0.5:
            sentiment_category = "EXCUBERANT"
        elif avg_sentiment_score >= 0.1:
            sentiment_category = "POSITIVE"
        elif avg_sentiment_score <= -0.5:
            sentiment_category = "PANIC"
        elif avg_sentiment_score <= -0.1:
            sentiment_category = "NEGATIVE"
            
        payload = {
            "ticker": ticker,
            "company_name": long_name,
            "cap_category": cap_cat,
            "current_price": current_price,
            "price_change_pct": price_change_pct,
            "fundamentals": {
                "market_cap": market_cap_str,
                "pe_ratio": pe_ratio,
                "roe": roe,
                "de_ratio": de_ratio,
                "dividend_yield": dividend_yield
            },
            "technicals": {
                "rsi": rsi_val,
                "macd": {
                    "macd": macd_val,
                    "signal": macd_sig,
                    "crossover": macd_cross
                },
                "bollinger_bands": {
                    "upper": upper_b_val,
                    "lower": lower_b_val,
                    "bandwidth": volatility_width,
                    "percent_b": pct_b_val
                },
                "fibonacci_618": fib_levels["fib_618"],
                "fibonacci_all": fib_levels,
                "moving_averages": {
                    "ema50": float(ema50),
                    "ema200": float(ema200),
                    "cross": ema_cross
                },
                "adx": {
                    "value": adx_val,
                    "regime": adx_regime
                },
                "breakout": breakout_alert
            },
            "sentiment": {
                "score": avg_sentiment_score,
                "category": sentiment_category
            },
            "risk_map": {
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk_reward": risk_reward_ratio
            },
            "news": news_headlines
        }
        
        return payload
    except Exception as e:
        import traceback
        print(f"[stock_agent] Quantitative math calculations error: {e}")
        traceback.print_exc()
        return None

def generate_general_advisor_reply(message, history):
    """
    Generates a conversational response as a professional advisor,
    reminding the user they can request a stock analysis.
    """
    system_prompt = (
        "You are a friendly, highly professional institutional investment advisor "
        "at StockVibe AI Elite Terminal. "
        "A user is chatting with you, but they have not named a specific stock ticker "
        "to run our quantitative analysis engine on. "
        "Respond to their message in a polite, helpful, and sophisticated tone. "
        "Ensure you answer their query if it is general financial/market chat, "
        "and gently remind them that they can type any Indian ticker (e.g. TCS, RELIANCE, COAL INDIA) "
        "or specific global tickers to generate a full institutional-grade real-time technical, "
        "fundamental, sentiment, and risk analysis report."
    )
    
    # Format history for LLM
    history_str = ""
    for msg in history[-5:]: # Keep last 5 messages
        history_str += f"{msg['role'].capitalize()}: {msg['content']}\n"
        
    user_prompt = f"{history_str}User: {message}\nAdvisor:"
    
    return call_llm(system_prompt, user_prompt, temperature=0.5)

def generate_institutional_report(payload):
    """
    Takes stock payload and feeds it into the LLM to format
    exactly as a 'StockVibe Elite Institutional Terminal AI' report.
    """
    system_prompt = (
        "You are the 'StockVibe Elite Institutional Terminal AI', a quant-driven analyst. "
        "Analyze the provided stock JSON payload and write a professional, institutional-grade research report. "
        "Format your entire response using the following structured Markdown categories and emojis. "
        "Ensure you format all numeric values, percentages, and tickers exactly as requested. "
        "Highlight important elements in neon/primary bold markers. "
        "Ensure you include all 9 sections exactly as written below:\n\n"
        
        "Format structure:\n"
        "### 🏢 Asset: [Company Name] ([TICKER]) | [Cap Category]\n"
        "### 💰 Current Price: ₹[Price] ([1D % Change]%)\n"
        "### 📐 Quantitative Technicals:\n"
        "- **Regime**: [Regime status, e.g., TRENDING BULLISH / RANGING]\n"
        "- **Momentum**: RSI at [RSI_VAL] ([RSI Condition, e.g. OVERBOUGHT/OVERSOLD/NEUTRAL]), MACD is [MACD_VAL] vs Signal [SIGNAL_VAL] ([MACD Crossover status])\n"
        "- **Bollinger Bands**: Upper ₹[Upper], Lower ₹[Lower] (Bandwidth: [Bandwidth]%, Current Pos: [Percent_B]%)\n"
        "- **EMAs Cross**: [Golden Cross/Death Cross status] (EMA50: ₹[EMA50] | EMA200: ₹[EMA200])\n"
        "- **Fibonacci 61.8% Level**: ₹[Fib_618_Val]\n"
        "- **Breakout Alerts**: [Breakout Status, e.g. BREAKOUT DETECTED / NO BREAKOUT]\n\n"
        
        "### 🏦 Fundamental Analysis:\n"
        "- **P/E Ratio**: [P/E] | **ROE**: [ROE] | **D/E Ratio**: [D/E]\n"
        "- **Dividend Yield**: [Dividend Yield] | **Market Valuation**: [Market Cap]\n\n"
        
        "### 🎭 Sentiment & Mood:\n"
        "- **Media Impact Score**: [Sentiment Score between -1.0 and 1.0] ([Sentiment Category, e.g. EXCUBERANT / PANIC])\n"
        "- **Summary**: Write a 2-sentence summary detailing current media coverage and headlines sentiment.\n\n"
        
        "### ⚠️ Trade Execution Map:\n"
        "- **Stop Loss**: ₹[Stop Loss]\n"
        "- **Take Profit**: ₹[Take Profit]\n"
        "- **Risk/Reward**: [Risk/Reward, e.g. 2.0:1 (Volatility Scaled)]\n\n"
        
        "### 🔮 Institutional Verdict: [BUY / SELL / HOLD] | **🎯 Alpha Confidence**: [Confidence]% \n\n"
        
        "### 📊 Deep Dive Synthesis:\n"
        "[Provide a dense, professional, 5-6 sentence confluence analysis synthesizing the technical regime, fundamental valuation health, news sentiment narrative, and risk-reward profile to justify the verdict.]\n\n"
        
        "### 🔗 Live Terminal:\n"
        "[View Live TradingView Chart](https://www.tradingview.com/symbols/NSE-{TICKER_ONLY}/) (Note: Ensure the ticker in TradingView URL is NSE-{TICKER_ONLY} for Indian stocks or regular symbol for US stocks, e.g., if ticker is TCS.NS, ticker_only is TCS)\n"
    )
    
    # Strip .NS or .BO for TradingView symbols
    ticker_only = payload['ticker'].split('.')[0]
    
    user_prompt = f"JSON Stock Payload:\n{payload}\n\nTradingView Symbol: {ticker_only}"
    
    report = call_llm(system_prompt, user_prompt, temperature=0.2)
    
    # If the response is NONE or empty, construct a fallback template using the payload data
    if report == "NONE" or len(report) < 100:
        report = construct_fallback_report(payload)
        
    return report

def construct_fallback_report(payload):
    """
    Constructs a structured report directly from the payload when LLM fails or is unavailable.
    """
    t = payload['ticker']
    t_only = t.split('.')[0]
    f = payload['fundamentals']
    tc = payload['technicals']
    rm = payload['risk_map']
    s = payload['sentiment']
    
    # Determine basic advice based on RSI and EMA
    verdict = "HOLD"
    confidence = 65
    if tc['rsi'] < 40 and tc['moving_averages']['cross'] == "GOLDEN CROSS":
        verdict = "BUY"
        confidence = 82
    elif tc['rsi'] > 70 and tc['moving_averages']['cross'] == "DEATH CROSS":
        verdict = "SELL"
        confidence = 78
    
    report = f"""### 🏢 Asset: {payload['company_name']} ({t}) | {payload['cap_category']}
### 💰 Current Price: ₹{payload['current_price']:.2f} ({payload['price_change_pct']:.2f}%)

### 📐 Quantitative Technicals:
- **Regime**: {tc['adx']['regime']} (ADX: {tc['adx']['value']:.1f})
- **Momentum**: RSI at {tc['rsi']:.1f} | MACD Crossover: {tc['macd']['crossover']}
- **Bollinger Bands**: Upper ₹{tc['bollinger_bands']['upper']:.2f}, Lower ₹{tc['bollinger_bands']['lower']:.2f} (Bandwidth: {tc['bollinger_bands']['bandwidth']*100:.1f}%)
- **EMAs Cross**: {tc['moving_averages']['cross']} (EMA50: ₹{tc['moving_averages']['ema50']:.2f} | EMA200: ₹{tc['moving_averages']['ema200']:.2f})
- **Fibonacci 61.8% Level**: ₹{tc['fibonacci_618']:.2f}
- **Breakout Alerts**: {tc['breakout']}

### 🏦 Fundamental Analysis:
- **P/E Ratio**: {f['pe_ratio']} | **ROE**: {f['roe']} | **D/E Ratio**: {f['de_ratio']}
- **Dividend Yield**: {f['dividend_yield']} | **Market Valuation**: {f['market_cap']}

### 🎭 Sentiment & Mood:
- **Media Impact Score**: {s['score']:.2f} ({s['category']})
- **Summary**: Media sentiment is currently {s['category']} with news headlines indicating stable to bullish interest.

### ⚠️ Trade Execution Map:
- **Stop Loss**: ₹{rm['stop_loss']:.2f}
- **Take Profit**: ₹{rm['take_profit']:.2f}
- **Risk/Reward**: {rm['risk_reward']}

### 🔮 Institutional Verdict: {verdict} | **🎯 Alpha Confidence**: {confidence}%

### 📊 Deep Dive Synthesis:
The quantitative signal engine has completed calculation for {payload['company_name']}. The stock shows a {tc['adx']['regime']} technical regime with RSI hovering at {tc['rsi']:.1f}. From a fundamental perspective, the P/E ratio is {f['pe_ratio']} with a return on equity of {f['roe']}. The news sentiment dictionary calculates a net {s['category']} posture. Incorporating Bollinger Band volatility parameters, stop-loss has been set at ₹{rm['stop_loss']:.2f} against a target of ₹{rm['take_profit']:.2f}, yielding a volatility-adjusted 2:1 risk-reward structure.

### 🔗 Live Terminal:
[View Live TradingView Chart](https://www.tradingview.com/symbols/NSE-{t_only}/)
"""
    return report
