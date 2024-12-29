from flask import Flask, render_template, request
import Login as fyers  # Assuming Login is your Fyers API module

app = Flask(__name__)


def round_to_two_decimal(value):
    """Helper function to round a number to two decimal places."""
    return round(value, 2)


def is_valid_symbol(symbol):
    """Check if the symbol is valid (does not contain BEES, ETF, or numerics)."""
    return not any(sub in symbol for sub in ["BEES", "ETF", "ALPHA"]) and not any(char.isdigit() for char in symbol)


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

        # Filter and round relevant fields in the holdings data
        filtered_holdings = []
        for holding in holdings_data:
            if is_valid_symbol(holding['symbol']):
                holding['costPrice'] = round_to_two_decimal(holding['costPrice'])
                holding['ltp'] = round_to_two_decimal(holding['ltp'])
                holding['marketVal'] = round_to_two_decimal(holding['marketVal'])
                holding['pl'] = round_to_two_decimal(holding['pl'])
                filtered_holdings.append(holding)

        holdings_data = filtered_holdings

    except Exception as e:
        holdings_data = f"Error fetching holdings: {str(e)}"

    return render_template("index.html", lp_value=lp_value, holdings=holdings_data)


if __name__ == "__main__":
    app.run(debug=True)
