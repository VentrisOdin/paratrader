import os
import requests
from dotenv import load_dotenv
import oandapyV20
import oandapyV20.endpoints.orders as orders
# Load environment variables from .env file
load_dotenv()

# OANDA API credentials
OANDA_API_URL = "https://api-fxpractice.oanda.com/v3"
OANDA_API_KEY = os.getenv("OANDA_API_KEY")
OANDA_ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")

def get_open_positions():
    """Fetch open positions from OANDA API."""
    url = f"{OANDA_API_URL}/accounts/{OANDA_ACCOUNT_ID}/openPositions"
    headers = {
        "Authorization": f"Bearer {OANDA_API_KEY}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching open positions: {response.status_code} - {response.text}")
        return []
    return response.json().get("positions", [])

def sell_position(instrument, units):
    """Close a position for a specific instrument."""
    url = f"{OANDA_API_URL}/accounts/{OANDA_ACCOUNT_ID}/orders"
    headers = {
        "Authorization": f"Bearer {OANDA_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "order": {
            "instrument": instrument,
            "units": str(-units),  # Negative units to sell
            "type": "MARKET",
            "positionFill": "REDUCE_ONLY"
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Error selling position for {instrument}: {response.status_code} - {response.text}")
    else:
        print(f"Sold position for {instrument}: {response.json()}")

def sell_all_positions():
    """Sell all open positions."""
    positions = get_open_positions()
    if not positions:
        print("No positions to sell.")
        return

    for position in positions:
        instrument = position["instrument"]
        units = int(position["long"]["units"]) - int(position["short"]["units"])
        if units != 0:
            sell_position(instrument, units)

    print("All positions sold.")

if __name__ == "__main__":
    sell_all_positions()