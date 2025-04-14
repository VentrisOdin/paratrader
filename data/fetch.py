import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OANDA_API_URL = os.getenv('OANDA_API_URL')
OANDA_API_KEY = os.getenv('OANDA_API_KEY')
OANDA_ACCOUNT_ID = os.getenv('OANDA_ACCOUNT_ID')

def fetch_instruments():
    url = f"{OANDA_API_URL}/v3/accounts/{OANDA_ACCOUNT_ID}/instruments"
    headers = {
        "Authorization": f"Bearer {OANDA_API_KEY}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        return [instrument['name'] for instrument in data.get("instruments", [])]

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching instruments: {e}")
        return []

def fetch_prices(instruments):
    url = f"{OANDA_API_URL}/v3/accounts/{OANDA_ACCOUNT_ID}/pricing"
    headers = {
        "Authorization": f"Bearer {OANDA_API_KEY}"
    }
    params = {
        "instruments": ','.join(instruments)
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        prices = data.get("prices", [])
        if not prices:
            print("No price data returned.")
            return

        for p in prices:
            instrument = p["instrument"]
            bids = p.get("bids", [])
            asks = p.get("asks", [])
            bid = float(bids[0]["price"]) if bids else None
            ask = float(asks[0]["price"]) if asks else None
            mid = (bid + ask) / 2 if bid and ask else None

            print(f"{instrument}: Bid={bid}, Ask={ask}, Mid={mid}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching pricing: {e}")

if __name__ == "__main__":
    instrument_list = fetch_instruments()
    if instrument_list:
        fetch_prices(instrument_list)
