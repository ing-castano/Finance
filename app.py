import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    holdings = db.execute("SELECT stock, shares FROM book WHERE user_id = ? ORDER BY stock", session["user_id"])
    total_holdings = 0.00

    for holding in holdings:
        quote = lookup(holding["stock"])
        if not quote:
            return redirect("/")
        holding["price"] = usd(quote["price"])
        holding["value"] = usd(quote["price"] * holding["shares"])
        total_holdings = (total_holdings + quote["price"] * holding["shares"])

    total_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])

    return render_template("index.html", holdings=holdings, total_cash=usd(total_cash[0]["cash"]), total_holdings=usd(total_holdings + total_cash[0]["cash"]))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")

        # Validate submit
        if not symbol:
            return apology("Must indicate symbol")
        if not request.form.get("shares"):
            return apology("Must indicate number of shares")
        if not lookup(symbol):
            return apology("Stock symbol "+symbol+" does not exists")
        if not request.form.get("shares").isdigit():
            return apology("Pleas provide a valid number of shares")
        else:
            shares = int(request.form.get("shares"))
            quote = lookup(symbol)
            if not quote:
                flash("Please try again")
                return render_template("buy.html")
            cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
            amount = quote["price"] * shares
            if cash[0]["cash"] < amount:
                return apology("Not enough cash in account")

            # Buy stock
            else:
                # Update transaction history table
                db.execute("INSERT INTO history (stock, price, date, shares, amount, user_id, type) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           symbol, quote["price"], datetime.now(), shares, amount, session["user_id"], "BUY")

                # Update stock portfolio
                # Check if user already have stock
                stock_exists = db.execute("SELECT stock FROM book WHERE stock = ? AND user_id = ?", symbol, session["user_id"])
                if stock_exists:
                    # Update symbol's shares
                    previous = db.execute("SELECT shares FROM book WHERE stock = ? AND user_id = ?", symbol, session["user_id"])
                    db.execute("UPDATE book SET shares = ? WHERE stock = ? AND user_id = ?",
                               float(previous[0]["shares"]) + shares, symbol, session["user_id"])
                else:
                    # Insert symbol
                    db.execute("INSERT INTO book (user_id, stock, shares) VALUES (?, ?, ?)",
                               session["user_id"], symbol, shares)

                # Update cash account
                db.execute("UPDATE users SET cash = ? WHERE id = ?", cash[0]["cash"] - amount, session["user_id"])
                flash("You have succesfully bought "+request.form.get("shares") +
                      " shares of "+quote["symbol"]+" at "+usd(quote["price"]))
                return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    rows = db.execute("SELECT type, stock, price, shares, date FROM history WHERE user_id = ?", session["user_id"])
    for row in rows:
        row["price"] = usd(row["price"])
    return render_template("history.html", rows=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        quote = lookup(symbol)
        print(quote)
        if not quote:
            return apology("Stock's Symbol Not Found", 400)
        return render_template("quoted.html", name=quote["name"], price=usd(quote["price"]), symbol=quote["symbol"])
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # Validation
        name = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        rows = db.execute("SELECT * FROM users WHERE username = ?", name)

        if not name or not password:
            return apology("Must provide valid username/password")
        elif password != confirmation:
            return apology("Password do not match")
        elif rows:
            return apology("Username is already taken")

        # New user registration
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", name, generate_password_hash(password))

        # User auto-login
        rows = db.execute("SELECT * FROM users WHERE username = ?", name)
        session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "POST":
        symbol = request.form.get("symbol")

        # Validate submission
        valid_symbol = db.execute("SELECT stock FROM book WHERE stock = ?", symbol)
        if not valid_symbol:
            return apology("Stock not found in your portfolio")
        if not request.form.get("shares").isdigit():
            return apology("Pleas provide a valid number of shares")
        shares = db.execute("SELECT shares FROM book WHERE user_id = ? AND stock = ?", session["user_id"], symbol)
        shares_to_sell = int(request.form.get("shares"))
        if shares_to_sell > shares[0]["shares"]:
            return apology("Amount of shares exceeds quantity owned")

        # Sell Stock
        # Update transaction history table
        quote = lookup(symbol)
        if not quote:
            flash("Please try again")
            return render_template("sell.html")
        amount = shares_to_sell * quote["price"]
        db.execute("INSERT INTO history (stock, price, date, shares, amount, user_id, type) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   symbol, quote["price"], datetime.now(), shares_to_sell, amount, session["user_id"], "SELL")

        # Update stock portfolio
        previous = db.execute("SELECT shares FROM book WHERE stock = ? AND user_id = ?", symbol, session["user_id"])
        if int(previous[0]["shares"]) == shares_to_sell:
            db.execute("DELETE FROM book WHERE user_id = ? AND stock = ?", session["user_id"], symbol)
        else:
            db.execute("UPDATE book SET shares = ? WHERE stock = ? AND user_id = ?",
                       float(previous[0]["shares"]) - shares_to_sell, symbol, session["user_id"])

        # Update cash account
        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash[0]["cash"] + amount, session["user_id"])
        flash("You have succesfully sold "+request.form.get("shares")+" shares of "+quote["symbol"]+" at "+usd(quote["price"]))
        return redirect("/")

    else:
        holdings = db.execute("SELECT stock FROM book WHERE user_id = ? GROUP BY stock", session["user_id"])
        return render_template("sell.html", holdings=holdings)


@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    """Personal Touch: Change user password"""
    if request.method == "POST":

        # Validation
        name = request.form.get("username")
        password = request.form.get("password")
        new_password = request.form.get("newpassword")
        new_confirmation = request.form.get("newconfirmation")
        rows = db.execute("SELECT * FROM users WHERE username = ?", name)

        if not name or not password or (not rows[0]["id"] == session["user_id"]) or not check_password_hash(rows[0]["hash"], password):
            return apology("Must provide valid username/password")
        elif new_password != new_confirmation:
            return apology("Passwords do not match")

        # Change user password
        db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(new_password), session["user_id"])
        flash("Password changed succesfully")
        return redirect("/")

    else:
        return render_template("changepass.html")