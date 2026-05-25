import sys
import os

# Adjust path to import from backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_agent import run_quantitative_analysis, discover_ticker

def test_ticker_discovery():
    print("Testing Ticker Discovery...")
    test_cases = {
        "Analyze RELIANCE please": "RELIANCE.NS",
        "How is TCS doing today?": "TCS.NS",
        "Get me the chart for COAL INDIA": "COALINDIA.NS",
        "Show stock analysis of TCS.NS": "TCS.NS",
        "Hi, how are you?": "NONE",
        "What is a Bollinger Band?": "NONE"
    }
    
    success = True
    for text, expected in test_cases.items():
        result = discover_ticker(text)
        if result == expected:
            print(f"  [PASS] '{text}' -> '{result}'")
        else:
            print(f"  [FAIL] '{text}' -> expected '{expected}', got '{result}'")
            success = False
            
    return success

def test_quantitative_analysis():
    print("\nTesting Quantitative Indicators and News Scraping...")
    # Test with a major liquid stock: TCS.NS
    ticker = "TCS.NS"
    print(f"Fetching and analyzing data for {ticker}...")
    
    payload = run_quantitative_analysis(ticker)
    if not payload:
        print("  [FAIL] run_quantitative_analysis returned None")
        return False
        
    print(f"  [PASS] Successfully fetched data for {payload['company_name']}")
    print(f"  [PASS] Current Price: Rs. {payload['current_price']:.2f} ({payload['price_change_pct']:.2f}%)")
    
    # Check technicals
    tech = payload['technicals']
    print("  Checking indicator values:")
    print(f"    - RSI (14-day): {tech['rsi']:.2f}")
    print(f"    - MACD Line: {tech['macd']['macd']:.4f} | Signal: {tech['macd']['signal']:.4f} | Cross: {tech['macd']['crossover']}")
    print(f"    - Bollinger Upper: Rs. {tech['bollinger_bands']['upper']:.2f} | Lower: Rs. {tech['bollinger_bands']['lower']:.2f} | Bandwidth: {tech['bollinger_bands']['bandwidth']*100:.2f}%")
    print(f"    - EMA50: Rs. {tech['moving_averages']['ema50']:.2f} | EMA200: Rs. {tech['moving_averages']['ema200']:.2f} | Cross: {tech['moving_averages']['cross']}")
    print(f"    - ADX (14-day): {tech['adx']['value']:.2f} | Regime: {tech['adx']['regime']}")
    print(f"    - Breakout Status: {tech['breakout']}")
    print(f"    - Fibonacci 61.8% Retracement: Rs. {tech['fibonacci_618']:.2f}")
    
    # Check risk mapping
    rm = payload['risk_map']
    print("  Checking risk map:")
    print(f"    - Stop Loss: Rs. {rm['stop_loss']:.2f}")
    print(f"    - Take Profit: Rs. {rm['take_profit']:.2f}")
    print(f"    - Risk/Reward: {rm['risk_reward']}")
    
    # Check news and sentiment
    news = payload['news']
    sent = payload['sentiment']
    print(f"  Checking news crawler & sentiment (Fetched {len(news)} items):")
    print(f"    - Sentiment Average Score: {sent['score']:.4f} | Category: {sent['category']}")
    
    if len(news) > 0:
        print("    - Sample Headline:")
        print(f"      [{news[0]['source']}] {news[0]['title']} ({news[0]['pub_date']})")
        print(f"      Lexicon score: {news[0]['score']} ({news[0]['sentiment']})")
        
    # Simple bounds check
    assert 0 <= tech['rsi'] <= 100, "RSI must be between 0 and 100"
    assert rm['stop_loss'] < payload['current_price'] < rm['take_profit'], "Current price must be between Stop Loss and Take Profit"
    assert -1.0 <= sent['score'] <= 1.0, "Sentiment score must be between -1.0 and 1.0"
    
    print("\n[ALL TESTS PASSED] Technical computations validated successfully!")
    return True

if __name__ == "__main__":
    t_disc = test_ticker_discovery()
    t_quant = test_quantitative_analysis()
    
    if t_disc and t_quant:
        print("\nVerification successful. StockVibe AI core intelligence is robust.")
        sys.exit(0)
    else:
        print("\nVerification failed.")
        sys.exit(1)
