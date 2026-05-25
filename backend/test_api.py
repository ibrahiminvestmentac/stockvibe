import requests
import json

url = "http://127.0.0.1:8080/api/chat"

def test_general_chat():
    print("Testing general conversation API...")
    payload = {
        "message": "Hi, who are you? What is this terminal?",
        "history": []
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        r = requests.post(url, headers=headers, json=payload)
        print("  Status code:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            print("  Response key present:", "response" in data)
            print("  Discovered ticker (should be null):", data.get("ticker"))
            print("  News count (should be 0):", len(data.get("news", [])))
            print("  Preview response:")
            print("---")
            print(data.get("response")[:200] + "...")
            print("---")
            return True
        else:
            print("  [FAIL] Status code:", r.status_code, r.text)
            return False
    except Exception as e:
        print("  [FAIL] Request failed:", e)
        return False

def test_stock_analysis():
    print("\nTesting stock analysis API (TCS)...")
    payload = {
        "message": "Analyze TCS please",
        "history": []
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        r = requests.post(url, headers=headers, json=payload)
        print("  Status code:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            print("  Response key present:", "response" in data)
            print("  Discovered ticker (should be TCS.NS):", data.get("ticker"))
            print("  News count (should be > 0):", len(data.get("news", [])))
            print("  Preview response:")
            print("---")
            print(data.get("response")[:300] + "...")
            print("---")
            return True
        else:
            print("  [FAIL] Status code:", r.status_code, r.text)
            return False
    except Exception as e:
        print("  [FAIL] Request failed:", e)
        return False

if __name__ == "__main__":
    c_gen = test_general_chat()
    c_stock = test_stock_analysis()
    if c_gen and c_stock:
        print("\n[SUCCESS] API endpoint tests completed successfully!")
    else:
        print("\n[FAILURE] API endpoint tests failed.")
