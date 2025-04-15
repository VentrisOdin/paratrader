import os
import oandapyV20
import oandapyV20.endpoints.orders as orders
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

# OANDA API credentials
api_key = os.getenv('OANDA_API_KEY')
account_id = os.getenv('OANDA_ACCOUNT_ID')

# Initialize the OANDA API client
client = oandapyV20.API(access_token=api_key)

def place_bid(instrument, units, order_type="MARKET", side="BUY"):
    """
    Places a market order (buy/sell) for the specified instrument.

    :param instrument: The trading pair (e.g., "EUR_USD")
    :param units: The number of units to buy/sell
    :param order_type: Type of order, default is "MARKET"
    :param side: "BUY" or "SELL"
    :return: Order response
    """
    order_data = {
        "order": {
            "units": units if side == "BUY" else -units,
            "instrument": instrument,
            "timeInForce": "FOK",  # "FOK" means Fill or Kill
            "type": order_type,
            "positionFill": "DEFAULT",
            "side": side
        }
    }

    # Place the order request
    try:
        response = client.request(orders.OrderCreate(account_id, data=order_data))
        print(f"Order successfully placed: {response}")
    except oandapyV20.exceptions.V20Error as e:
        print(f"Error placing order: {e}")

# Example usage
place_bid("EUR_USD", 1000, side="BUY")  # Buys 1000 units of EUR/USD
