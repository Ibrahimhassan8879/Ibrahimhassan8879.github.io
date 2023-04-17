import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from pytz import timezone
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

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


@app.route("/", methods = ["GET"])
@login_required
def index():
    """Show portfolio of stocks"""
    "check if the user is new"

    rows = db.execute("SELECT * FROM stocks WHERE user_id = ?",session["user_id"])
    total_spent = 0
    if len(rows) == 0:
        return render_template("/index.html")

    for row in rows:
        Valid_data = lookup(row['symbol'])
        for key in Valid_data:
            row[key] = Valid_data[key]

        row['total'] = round(row['shares'] * row['price'],2)
        total_spent += row['total']

    cash = db.execute("SELECT cash FROM users WHERE id = ?" , session["user_id"])
    cash = round(cash[0]['cash'],2)
    total_money =  round(total_spent,2)
    return render_template("/index.html",stocks = rows , total = total_money , cash = cash )


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    "GET WEBPAGE VIA GET"
    if request.method == "GET":
        return render_template("buy.html")

    "GET WEBPAGE VIA POST"
    if request.method == "POST":
        "lookup function returns"

        Valid_data = lookup(request.form.get("symbol"))

        "data gathering"
        symbol = Valid_data["symbol"]
        price  = Valid_data["price"]
        name   = Valid_data["name"]
        "check symbol entry"
        if symbol == None:
            return apology("The symbol doesn't exist !")
        "check share entry or negative"
        shares = int(request.form.get("shares"))
        if not shares:
            return apology("Plase Enter the amount you want to buy !")
        if shares < 0:
            return apology("Please Enter Positive integer")

        purshase = price * shares
        "user account cash"
        user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"] )
        user_cash = user_cash[0]['cash']
        user_cash_after_purshase = user_cash - purshase

        if user_cash_after_purshase < 0:
            return apology("There is not enough money")

        "transaction making & saving"

        "update user_account cash"
        db.execute("UPDATE users SET cash = ? WHERE id = ?",user_cash_after_purshase,session["user_id"])

        "check putting data for the first time"
        rows = db.execute("SELECT * FROM stocks WHERE user_id = ? AND symbol = ?",session["user_id"],symbol)

        "Generate transaction NO"
        transaction_ID = db.execute("INSERT INTO user_transactions(user_id) VALUES(?)",session["user_id"])

        "Put data into transactions table"
        db.execute("INSERT INTO transactions(user_id,symbol,name,shares,price,type,transaction_id) VALUES (?,?,?,?,?,?,?)",session["user_id"],symbol,name,shares,price,"Buy",transaction_ID)

        if len(rows) != 1:
            db.execute("INSERT INTO stocks(user_id,symbol,shares) VALUES (?,?,?)",session["user_id"],symbol,shares)

            "if not the first time put data normally keep update only shares"
        else:
            shares_old = db.execute("SELECT shares FROM stocks WHERE user_id = ? AND symbol = ?",session["user_id"],symbol)
            shares_old = shares_old[0]['shares']
            new_shares = shares_old + shares
            db.execute("UPDATE stocks SET shares = ? WHERE user_id = ? AND symbol = ? ",new_shares,session["user_id"],symbol)
    return redirect("/")


@app.route("/history", methods=["GET"])
@login_required
def history():
    """Show history of transactions"""
    "Transactions Variables"
    stocks = db.execute("SELECT * FROM transactions WHERE user_id = ?",session["user_id"])

    for stock in stocks:
        Valid_data = lookup(stock["symbol"])
        for key in Valid_data:
            stock[key]=Valid_data[key]

    if len(stocks) == 0:
        return apology("you haven't bought anything yet")

    for stock in stocks:
        stock = db.execute("SELECT transaction_id FROM transactions WHERE user_id = ?",session["user_id"])[0]

    return render_template("/history.html",stocks = stocks)


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

@app.route("/resetpassword", methods=["GET", "POST"])
def resetpassword():
    if request.method == "GET":
        return render_template("resetpassword.html")
    else:
        username_check = request.form.get("username")
        username = db.execute("SELECT * from users WHERE username = ?", username_check )
        if len(username) != 1:
            return apology("Username you've entered doesn't exist")
        else:
            new_password = request.form.get("resetpassword")
            passwordconfirmation= request.form.get("passwordconfirmation")
            if new_password != passwordconfirmation:
                return apology("Passwords must be the same")

            old_password = db.execute("SELECT hash FROM users WHERE username = ?",username_check)
            same_password = check_password_hash(old_password,new_password)
            if same_password == 0:
                return apology("Password can't be the same as the old one !")

            hash_pass = generate_password_hash(new_password)
            db.execute("UPDATE users SET hash = ? WHERE username = ?",hash_pass,request.form.get("username"))
            return redirect("/")

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
    if request.method == "GET":
        return render_template("quote.html")
    else :
        symbol = lookup(request.form.get("symbol"))
        if not symbol:
            return apology("The symbol you've entered is not available")
        else:
            name = symbol["name"]
            price = symbol["price"]
            symbol = symbol["symbol"]
            return render_template("quoted.html", name=name , price=price , symbol = symbol)


@app.route("/register", methods=["GET", "POST"])
def register():

    #forget any user_id
    session.clear()

    if request.method == "GET":
        render_template("/register.html")

    if request.method == "POST":

        #New username entry
        username = request.form.get("username")

        #Blank username
        if not request.form.get("username"):
            return apology("User name is requried")

        #checking for indentical username
        userdata = db.execute("SELECT * from users WHERE username = ?",request.form.get("username"))
        if len(userdata) == 1:
            return apology("User name has already taken !")

        #Blank password
        if not request.form.get("password"):
            return apology("Password is not set !")

        #Password & it's confirmation not the same
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Password fields must me the same characters !")

        #Password hashing
        password = generate_password_hash(request.form.get("password"))

        #checking for indentical Email
        email = request.form.get("email")
        mails = db.execute("SELECT * from users WHERE email = ?",email)
        if len(mails) == 1:
            return apology("Email Has already been regiestered !")

        #Phone number
        phone_number = request.form.get("phone_number")
        phone_numbers = db.execute("SELECT * FROM users WHERE phone_number = ?",phone_number)

        if phone_number.isnumeric() == False:
            return apology("Phone number is invalid")
        if len(phone_numbers) == 1:
            return apology("Phone number already has been regiestered!")

        #Account Data insertion
        db.execute("INSERT INTO users (username,hash,email,phone_number) VALUES (?)",(username,password,email,phone_number))

        #Aquiring session
        return redirect("/")

    #User getting page
    return render_template("/register.html")





@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    #User getting page & stocks gathering
    if request.method == "GET":
        stocks = db.execute("SELECT * FROM stocks WHERE user_id = ?",session["user_id"])
        return render_template("sell.html",stocks = stocks)

    #User Posting
    if request.method == "POST":

        Sold_stock = request.form.get("item_sold")

        #stock searching & checking availability
        stock = db.execute("SELECT * FROM stocks WHERE user_id = ? AND symbol = ?",session["user_id"],Sold_stock)
        if len(stock) != 1:
            return apology("Please Select a valid stock on your account")

        #stock checking quantity
        quantity_sold = int(request.form.get("shares"))
        quantity_available = db.execute("SELECT shares FROM stocks WHERE user_id = ? AND symbol = ?",session["user_id"],Sold_stock)
        quantity_available = quantity_available[0]['shares']
        if quantity_sold > quantity_available:
            return apology("Cannot sell more than the stocks available")
        new_quantity_share = quantity_available - quantity_sold

        #stock selling & cash back
        unit_sold_price = lookup(Sold_stock)
        unit_sold_price = unit_sold_price['price']

        #New cash saving into account
        cash_back = unit_sold_price * quantity_sold
        cash_available = db.execute("SELECT cash FROM users WHERE id = ?",session["user_id"])
        cash_available = cash_available[0]['cash']
        cash_after_selling = cash_available + cash_back
        db.execute("UPDATE users SET cash = ? WHERE id = ?",cash_after_selling,session["user_id"])

        #Update shares quantity into stocks
        db.execute("UPDATE stocks SET shares = ? WHERE user_id = ? AND symbol = ?",new_quantity_share,session["user_id"],Sold_stock)

        return redirect("/")
