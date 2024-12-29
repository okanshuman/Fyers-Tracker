from flask import Flask, render_template, request, jsonify
import Login as fyers  # Assuming Login is your Fyers API module

app = Flask(__name__)

# Global set to keep track of processed symbols
processed_symbols = set()


def round_to_two_decimal(value):
    """Helper function to round a number to two decimal places."""
    return round(value, 2)


def is_valid_symbol(symbol):
    """Check if the symbol is valid (does not contain BEES, ETF, ALPHA, MAFANG, MOREALTY, MOMOMENTUM, or numerics)."""
    return not any(sub in symbol for sub in ["BEES", "ETF", "ALPHA", "MAFANG", "MOREALTY", "MOMOMENTUM"]) and not any(
        char.isdigit() for char in symbol)


def clean_symbol(symbol):
    """Remove 'NSE:' prefix and '-EQ' suffix from the symbol."""
    return symbol.replace("NSE:", "").replace("-EQ", "")


def calculate_percentage_change(cost_price, ltp):
    """Calculate the percentage change based on cost price and last traded price."""
    if cost_price == 0:
        return 0.0  # Avoid division by zero
    return round_to_two_decimal(((ltp - cost_price) / cost_price) * 100)


@app.route("/", methods=["GET", "POST"])
def index():
    lp_value = None  # Initialize the lp value
    holdings_data = None  # Initialize holdings data

    if request.method == "POST":
        stock_symbol = request.form.get("stock_symbol")
        stock_symbol = stock_symbol.upper()
        if stock_symbol:
            data = {"symbols": f"NSE:{stock_symbol}-EQ"}
            try:
                response = fyers.fyers_active.quotes(data)
                lp_value = round_to_two_decimal(response['d'][0]['v']['lp'])  # Extract and round lp value
            except Exception as e:
                lp_value = f"Error fetching data: {str(e)}"

    # Fetch current holdings
    try:
        holdings_response = fyers.fyers_active.holdings()
        holdings_data = holdings_response['holdings']  # Extracting only holdings

        # Filter, clean, and round relevant fields in the holdings data
        filtered_holdings = []
        for holding in holdings_data:
            if is_valid_symbol(holding['symbol']):
                holding['symbol'] = clean_symbol(holding['symbol'])  # Clean the symbol
                holding['costPrice'] = round_to_two_decimal(holding['costPrice'])
                holding['ltp'] = round_to_two_decimal(holding['ltp'])
                holding['pl'] = round_to_two_decimal(holding['pl'])
                holding['marketVal'] = round_to_two_decimal(
                    holding.get('marketVal', 0))  # Ensure marketVal is rounded too

                # Calculate percentage change and add it to the holding data
                holding['percentChange'] = calculate_percentage_change(holding['costPrice'], holding['ltp'])

                filtered_holdings.append(holding)

        # Sort holdings by percentage change in increasing order
        filtered_holdings.sort(key=lambda x: x['percentChange'])

        holdings_data = filtered_holdings

        # Place orders for symbols with % change greater than -5%
        for holding in filtered_holdings:
            if holding['percentChange'] > -5:  # Adjusted condition to >-5%
                order_symbol = f"NSE:{holding['symbol']}-EQ"  # Format as required

                # Check if this symbol has already been processed
                if holding['symbol'] not in processed_symbols:
                    order_data = {
                        "symbol": order_symbol,
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

                    # Add this symbol to the processed list
                    processed_symbols.add(holding['symbol'])

    except Exception as e:
        holdings_data = f"Error fetching holdings: {str(e)}"

    return render_template("index.html", lp_value=lp_value, holdings=holdings_data)


@app.route("/update_holdings", methods=["GET"])
def update_holdings():
    """Fetch updated holdings and return as JSON."""
    try:
        holdings_response = fyers.fyers_active.holdings()
        holdings_data = holdings_response['holdings']

        # Process and clean relevant fields
        filtered_holdings = []
        for holding in holdings_data:
            if is_valid_symbol(holding['symbol']):
                holding['symbol'] = clean_symbol(holding['symbol'])
                holding['costPrice'] = round_to_two_decimal(holding['costPrice'])
                holding['ltp'] = round_to_two_decimal(holding['ltp'])
                holding['pl'] = round_to_two_decimal(holding['pl'])
                holding['percentChange'] = calculate_percentage_change(holding['costPrice'], holding['ltp'])

                filtered_holdings.append(holding)

        filtered_holdings.sort(key=lambda x: x['percentChange'])  # Sort by percent change

        return jsonify(filtered_holdings)  # Return as JSON response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
