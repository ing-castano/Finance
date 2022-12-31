import os
import requests
import urllib.parse
import yfinance
import alpha_vantage

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={urllib.parse.quote_plus(symbol)}&apikey=OH4NNM3ZQLQY8L2J"
        url_overview = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={urllib.parse.quote_plus(symbol)}&apikey=OH4NNM3ZQLQY8L2J"

        response = requests.get(url)
        response.raise_for_status()

        response_ov = requests.get(url_overview)
        response_ov.raise_for_status()
        
    except requests.RequestException:
        return None

    # Parse response
    try: 
        quote = response.json()
        quote_ov = response_ov.json()
        return {
            "name": quote_ov['Name'],
            "price": float(quote['Global Quote']['05. price']),
            "symbol": quote['Global Quote']['01. symbol']
        }
    except (KeyError, TypeError, ValueError):
        return None


"""    # Contact API
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={urllib.parse.quote_plus(symbol)}&apikey=OH4NNM3ZQLQY8L2J"
        print(f"URL={url}")
        response = requests.get(url)
        print(response)
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        #ticket = yfinance.Ticker(symbol)
        return {
            "name": 'ticket.info["longName"]',
            "price": float(quote["05. price"]),
            "symbol": symbol
        }
    except (KeyError, TypeError, ValueError):
        return None
"""
"""
    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None
"""

def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
