import os
from dotenv import load_dotenv

load_dotenv()
gkey = os.environ.get("GEMINI_API_KEY")
print("GEMINI_API_KEY loaded:", gkey is not None)
if gkey:
    print("Length of key:", len(gkey))
    print("Starts with:", gkey[:7])
else:
    print("Key is None!")
