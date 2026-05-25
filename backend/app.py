import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from stock_agent import discover_ticker, run_quantitative_analysis, generate_institutional_report, generate_general_advisor_reply

# Load environment variables
load_dotenv()

# Set up Flask app. Serve frontend static assets from ../frontend
app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)

@app.route('/')
def index():
    """Serves the main application landing page."""
    return app.send_static_file('index.html')

@app.route('/api/debug', methods=['GET'])
def debug():
    ticker = request.args.get('ticker', 'TCS.NS')
    try:
        import yfinance as yf
        import requests
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        stock = yf.Ticker(ticker, session=session)
        df = stock.history(period="2y")
        info = stock.info if stock.info else {}
        return jsonify({
            "status": "success",
            "ticker": ticker,
            "df_empty": df.empty,
            "df_rows": len(df) if not df.empty else 0,
            "df_columns": list(df.columns) if not df.empty else [],
            "info_keys": list(info.keys()) if info else [],
            "info_name": info.get('longName') if info else None
        })
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main conversational agent routing.
    Accepts: { message: str, history: [ {role: str, content: str} ] }
    Returns: { response: str, ticker: str|null, news: list }
    """
    try:
        data = request.get_json() or {}
        message = data.get('message', '').strip()
        history = data.get('history', [])
        
        if not message:
            return jsonify({"error": "Empty message"}), 400
            
        print(f"[app] Received message: '{message}'")
        
        # 1. Ticker discovery
        ticker = discover_ticker(message)
        print(f"[app] Discovered ticker: {ticker}")
        
        if ticker != "NONE":
            # 2. Run Quantitative and News Sentiment Engine
            payload = run_quantitative_analysis(ticker)
            
            if payload:
                # 3. Generate structured institutional report
                report = generate_institutional_report(payload)
                return jsonify({
                    "response": report,
                    "ticker": ticker,
                    "news": payload.get('news', [])
                })
            else:
                # Fallback if yfinance failed or returned empty
                fallback_msg = (
                    f"I detected that you were asking about **{ticker}**, but I was unable to retrieve "
                    "sufficient historical market data or company parameters from the financial feeds. "
                    "Please verify that the ticker is correct, active on public exchanges, and try again."
                )
                return jsonify({
                    "response": fallback_msg,
                    "ticker": ticker,
                    "news": []
                })
        else:
            # 4. General conversational chat
            advisor_reply = generate_general_advisor_reply(message, history)
            if advisor_reply == "NONE" or not advisor_reply:
                advisor_reply = (
                    "Welcome to **StockVibe Elite Terminal**. I was unable to connect to the AI model "
                    "(please verify that a valid Gemini/Groq API key is configured in your `.env` file).\n\n"
                    "However, you can still type any stock ticker or company name (e.g., **TCS**, **RELIANCE**, **COAL INDIA**) "
                    "to trigger our fully local quantitative engine. It will compute Technical Indicators, Fibonacci Levels, "
                    "Bollinger Bands, Volatility-Scaled Risk Parameters, and scrape real-time headlines with lexicon-based sentiment analysis!"
                )
            return jsonify({
                "response": advisor_reply,
                "ticker": None,
                "news": []
            })
            
    except Exception as e:
        print(f"[app] Error in /api/chat endpoint: {e}")
        return jsonify({
            "error": "Internal Server Error",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    print(f"Starting StockVibe AI Backend Terminal on http://127.0.0.1:{port} (static: {app.static_folder})")
    app.run(host='0.0.0.0', port=port, debug=debug_mode, use_reloader=False)
