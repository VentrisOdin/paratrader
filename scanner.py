
import os
import requests
from dotenv import load_dotenv
import time
from divergence import track_divergence
  
# Load environment variables from .env file
load_dotenv()
# add lines for git upload
# OANDA API credentials
API_KEY = os.getenv("OANDA_API_KEY")
BASE_URL = "https://api-fxpractice.oanda.com/v3"

# Headers for API requests
HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

def get_instruments():
    """Fetch all available instruments (currency pairs) from OANDA."""
    url = f"{BASE_URL}/accounts/{os.getenv('OANDA_ACCOUNT_ID')}/instruments"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("instruments", [])
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []

def fetch_market_data(instrument_name):
    """Fetch market data (candlesticks) for a specific instrument."""
    url = f"{BASE_URL}/instruments/{instrument_name}/candles"
    params = {
        "count": 100,  # Number of candlesticks to fetch
        "granularity": "H1"  # Hourly candlesticks
    }
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json().get("candles", [])
    else:
        print(f"Error fetching data for {instrument_name}: {response.status_code} - {response.text}")
        return []


def scan_and_analyze():
    """Scan currency pairs, fetch market data, and analyze for divergence."""
    instruments = get_instruments()
    for instrument in instruments:
        print(f"Scanning {instrument['name']}...")
        candles = fetch_market_data(instrument['name'])
        if detect_divergence(candles):
            print(f"Divergence detected in {instrument['name']}! Investigate further.")

if __name__ == "__main__":
    # Uncomment one of the following blocks to run the desired functionality:

    # Run scan_currency_pairs to print details of all currency pairs
    # scan_currency_pairs()

    # Run scan_and_analyze in a loop to detect divergence
    while True:
        scan_and_analyze()
        time.sleep(3600)  # Wait for an hour before the next scan
        # Import the divergence detection logic from divergence.py

        # Modify detect_divergence to use the imported logic
def detect_divergence(candles):
    return is_bullish_divergence(candles)

        # Run the scan_and_analyze function
        scan_and_analyze()