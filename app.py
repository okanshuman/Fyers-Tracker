from flask import Flask, render_template, request
import Login as Fyers  # Assuming Login is your Fyers API module

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    lp_value = None  # Initialize the lp value
    if request.method == "POST":
        stock_symbol = request.form.get("stock_symbol")
        stock_symbol = stock_symbol.upper()
        if stock_symbol:
            data = {"symbols": f"NSE:{stock_symbol}-EQ"}
            try:
                response = Fyers.fyers_active.quotes(data)
                lp_value = response['d'][0]['v']['lp']  # Extract lp value
            except Exception as e:
                lp_value = f"Error fetching data: {str(e)}"

    return render_template("index.html", lp_value=lp_value)

if __name__ == "__main__":
    app.run(debug=True)
