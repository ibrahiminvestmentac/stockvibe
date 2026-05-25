import requests

url = "https://stockvibe-vg5w.onrender.com/api/chat"

def test_live_chat(message):
    print(f"Testing live API chat with message: '{message}'...")
    payload = {
        "message": message,
        "history": []
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=25)
        print("  Status code:", r.status_code)
        if r.status_code == 200:
            try:
                data = r.json()
                print("  Response key present:", "response" in data)
                print("  Discovered ticker:", data.get("ticker"))
                print("  News count:", len(data.get("news", [])))
                print("  Preview response:")
                print("---")
                # Clean up unicode printing for Windows console
                clean_resp = data.get("response", "").replace("₹", "Rs. ").replace("🏢", "[Company]").replace("💰", "[Price]").replace("📐", "[Technical]").replace("🏦", "[Fundamental]").replace("🎭", "[Sentiment]").replace("⚠️", "[Risk]").replace("🔮", "[Verdict]").replace("📊", "[Synthesis]").replace("🔗", "[Link]")
                print(clean_resp[:400] + "...")
                print("---")
            except Exception as e:
                print("  [ERROR] Parsing JSON response:", e)
                print("  Raw response text:", r.text[:500])
        else:
            print("  [FAIL] HTTP error:", r.status_code)
            print("  Raw response:", r.text[:500])
    except Exception as e:
        print("  [FAIL] Connection failed:", e)

if __name__ == "__main__":
    test_live_chat("Hello, what is this terminal?")
    test_live_chat("Analyze TCS")
