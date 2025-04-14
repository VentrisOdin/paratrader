# main.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OANDA_API_KEY")
ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")
ACCOUNT_TYPE = os.getenv("OANDA_ACCOUNT_TYPE")  # Should be fxpractice or fxtrade

BASE_URL = f"https://api-{ACCOUNT_TYPE}.oanda.com/v3"

def get_account_info():
    url = f"{BASE_URL}/accounts/{ACCOUNT_ID}"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    print("URL:", url)
    print("Headers:", headers)

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("✅ Connected successfully. Account info:")
        print(response.json())
    else:
        print(f"❌ Failed to connect. Status code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    get_account_info()
