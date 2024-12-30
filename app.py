# app.py
from flask import Flask, render_template, jsonify
from flask_apscheduler import APScheduler
import Login as fyers
from utils import round_to_two_decimal, is_valid_symbol, clean_symbol, calculate_percentage_change

app = Flask(__name__)
scheduler = APScheduler()

# Global variable to store holdings data and processed symbols
holdings_data = []
processed_symbols = set()  # To track symbols for which orders have been placed

def fetch_holdings():
    """Fetch current holdings and update global holdings_data."""
    global holdings_data
    try:
        holdings_response = fyers.fyers_active.holdings()
        holdings_data = holdings_response['holdings']

        # Initialize total profit/loss
        total_pl = 0.0

        # Filter, clean, and round relevant fields in the holdings data
        filtered_holdings = []
        for holding in holdings_data:
            if is_valid_symbol(holding['symbol']):
                holding['symbol'] = clean_symbol(holding['symbol'])
                holding['costPrice'] = round_to_two_decimal(holding['costPrice'])
                holding['ltp'] = round_to_two_decimal(holding['ltp'])
                holding['pl'] = round_to_two_decimal(holding['pl'])
                holding['marketVal'] = round_to_two_decimal(holding.get('marketVal', 0))

                # Calculate percentage change and add it to the holding data
                holding['percentChange'] = calculate_percentage_change(holding['costPrice'], holding['ltp'])

                # Update total profit/loss
                total_pl += holding['pl']

                filtered_holdings.append(holding)

        # Sort holdings by percentage change in increasing order
        filtered_holdings.sort(key=lambda x: x['percentChange'])

        # Place orders for symbols with % change greater than -5%
        for holding in filtered_holdings:
            if holding['percentChange'] > -5 and holding[
                'symbol'] not in processed_symbols:  # Check if order has already been placed
                order_data = {
                    "symbol": f"NSE:{holding['symbol']}-EQ",  # Format as required
                    "qty": holding['quantity'],  # Use quantity from holdings
                    "type": 2,
                    "side": -1,
                    "productType": "CNC",
                    "limitPrice": 0,
                    "stopPrice": 0,
                    "validity": "DAY",
                    "disclosedQty": 0,
                    "offlineOrder": False,
                    "orderTag": "tag1"
                }
                response = fyers.fyers_active.place_order(data=order_data)
                print(f"Order placed for {holding['symbol']}: {response}")

                # Add symbol to processed set to prevent re-ordering
                processed_symbols.add(holding['symbol'])

        holdings_data = filtered_holdings

        return round_to_two_decimal(total_pl)  # Round the total P&L before returning

    except Exception as e:
        print(f"Error fetching holdings: {str(e)}")
        return 0.0  # Return zero if there's an error

@app.route("/", methods=["GET"])
def index():
    """Render the index page with current holdings."""
    total_pl = fetch_holdings()  # Fetch holdings and get total P&L
    return render_template("index.html", holdings=holdings_data, total_pl=total_pl)

@app.route("/update_holdings", methods=["GET"])
def update_holdings():
    """Return current holdings data as JSON."""
    return jsonify(holdings_data)  # Return current holdings data as JSON

@scheduler.task('interval', id='update_holdings_task', seconds=15)
def scheduled_update():
    fetch_holdings()

if __name__ == "__main__":
    scheduler.init_app(app)
    scheduler.start()
    fetch_holdings()  # Initial fetch of holdings when starting the app
    app.run(debug=False,host='0.0.0.0', port=5001)  # Set debug=True for development purposes
