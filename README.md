# Finance
Brief simulation of buy - selling finance web.app with API stock information

## Requirements
* cs50 library
* Flask extension
* Flask-Session library
* requests library
* werkzeug.security library
* datetime library

## Testing
Run a flask server under `flask run` cmd in terminal window. Folders are provided to run under flask configuration (~/templates ~/static
~/app.py)

## Specifications
This is a flask web application that let the user sign in with an initial cash of 10.000usd, buy / sell any stock, view it's user transaction history and the total holding value of open positions + cash.

## Features
### ~/templates 
Has all the html files to display user front-end experience. Design with Bootstrap 5.0 framework, there is a `layout.html` files with the navbar and default options. The rest of the files, are a Jinja extension of the body part.

### ~/static
Some of the style is personalized under CSS own stylesheet.

### Server logic files
By the use of two files, *app.py* and *helpers.py* holds the server configuration to sign in - log in/out user, save user transactions, buy and sell stocks and ask for actual price.

Session files let the user stay logged in using local machine systema cookies.

`app.py` - Holds the logic to: 
* `@app.route("/")` show current stocks
* `@app.route("/buy")` buy stocks
* `@app.route("/sell")`sell stocks
* `@app.route("/register")` - `@app.route("/login")` - `@app.route("/logout")` register/logs user
* `@app.route("/history")`show all the transactions from logged user
* `@app.route("/quote")`show the current price of the selected stock
* `@app.route("/change_password")`let the user change the password


`helpers.py` - Holds some auxiliary functions as:
* `apology` function: Run memegen from jace browning github project to automate user msgs
* `login_required` function: Decorated function to prevent unlogged user to access certain functionalities
* `lookup` function: Uses Alpha Vantage API to ask for stock financial information. API key is free and is already loaded into the .py file.
* `usd` function: Format function to style float with USD money style.

### SQL Databases
#### users table
* id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL
* username TEXT NOT NULL
* hash TEXT NOT NULL
* cash NUMERIC NOT NULL DEFAULT 10000.00);

CREATE UNIQUE INDEX username ON users (username);


#### book table
* id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL
* user_id INTEGER NOT NULL
* stock TEXT NOT NULL
* shares INTEGER NOT NULL


#### history table
* id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL
* stock TEXT NOT NULL
* price INTEGER NOT NULL
* date DATETIME NOT NULL
* shares INTEGER NOT NULL
* amount INTEGER NOT NULL
* user_id INTEGER NOT NULL
* type TEXT

CREATE INDEX user_id ON history(user_id);


