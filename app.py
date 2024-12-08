from flask import Flask, request, session, redirect, url_for, render_template
from flaskext.mysql import MySQL
import pymysql
import re
import yaml

app = Flask(__name__)
mysql = MySQL()
db = yaml.safe_load(open('db.yaml'))

print(db)

app.config['MYSQL_DATABASE_HOST'] = db['mysql_host']
app.config['MYSQL_DATABASE_USER'] = db['mysql_user']
app.config['MYSQL_DATABASE_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DATABASE_DB'] = db['mysql_db']

mysql.init_app(app)

# change this to your secret key
# (can be anything, it's for extra protection)
app.secret_key = "feitian"


# http://localhost:5000/login/ - this will be the login page
@app.route("/login/", methods=["GET", "POST"])
def login():

    # connect
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # output message if something goes wrong...
    msg = ""

    # check if "username" and "password" POST requests exist (user submitted form)
    if (request.method == "POST"
        and "username" in request.form
        and "password" in request.form):

        # create variables for easy access
        username = request.form["username"]
        password = request.form["password"]

        # check if account exists using MySQL
        cursor.execute(
            "SELECT * FROM accounts WHERE username = %s AND password = %s",
            (username, password),
        )

        # fetch one record and return result
        account = cursor.fetchone()

        # if account exists in accounts table in out database
        if account:
            # create session data, we can access this data in other routes
            session["loggedin"] = True
            session["id"] = account["id"]
            session["username"] = account["username"]

            # redirect to home page
            # return 'Logged in successfully!'
            return redirect(url_for("home"))

        else:
            # account doesnt exist or username/password incorrect
            msg = "Incorrect username/password!"

    return render_template("index.html", msg=msg)


# http://localhost:5000/register - this will be the registration page
@app.route("/register", methods=["GET", "POST"])
def register():
    # connect
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # output message if something goes wrong...
    msg = ""
    # check if "username", "password" and "email" POST requests exist (user submitted form)
    if (request.method == "POST"
        and "username" in request.form
        and "password" in request.form
        and "email" in request.form):

        # create variables for easy access
        fullname = request.form["fullname"]
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]

        # check if account exists using MySQL
        cursor.execute("SELECT * FROM accounts WHERE username = %s", (username))
        account = cursor.fetchone()

        # if account exists show error and validation checks
        if account:
            msg = "Account already exists!"
        #Validation through javascript in register.html
        #elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            #msg = "Invalid email address!"
        elif not re.match(r"[A-Za-z0-9]+", username):
            msg = "Username must contain only characters and numbers!"
        #Validation through javascript in register.html
        #elif not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@.$!%*?&])[A-Za-z\d@.$!%*?&]{8,}$', password):
           # msg = "Password must be 8+ characters with uppercase, lowercase, number, and special character!"
        elif not username or not password or not email:
            msg = "Please fill out each sections!"
        else:
            # account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute(
                "INSERT INTO accounts (fullname, username, password, email) VALUES (%s, %s, %s, %s)",
                (fullname, username, password, email),
            )


            conn.commit()
            msg = "You have successfully registered!"

    elif request.method == "POST":
        # form is empty... (no POST data)
        msg = "Please fill out the form!"

    # show registration form with message (if any)
    return render_template("register.html", msg=msg)


# http://localhost:5000/home - this will be the home page, only accessible for loggedin users
@app.route("/")
def home():
    # check if user is loggedin
    if "loggedin" in session:
        # user is loggedin show them the home page
        return render_template("home.html", username=session["username"])

    # user is not loggedin redirect to login page
    return redirect(url_for("login"))


# http://localhost:5000/logout - this will be the logout page
@app.route("/logout")
def logout():
    # remove session data, this will log the user out
    session.pop("loggedin", None)
    session.pop("id", None)
    session.pop("username", None)

    # redirect to login page
    return redirect(url_for("login"))


# http://localhost:5000/profile - this will be the profile page, only accessible for loggedin users
@app.route("/profile")
def profile():
    # check if account exists using MySQL
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # check if user is loggedin
    if "loggedin" in session:
        # we need all the account info for the user so we can display it on the profile page
        cursor.execute("SELECT * FROM accounts WHERE id = %s", [session["id"]])
        account = cursor.fetchone()

        # show the profile page with account info
        return render_template("profile.html", account=account)

    # user is not loggedin redirect to login page
    return redirect(url_for("login"))

@app.route("/settings", methods=["GET", "POST"])
def settings():
    # Connect to the database
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # Check if the user is logged in
    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to login if not logged in

    username = session["username"]  # Get the logged-in user's username

    # Retrieve the current user details
    cursor.execute("SELECT * FROM accounts WHERE username = %s", (username,))
    account = cursor.fetchone()

    # If the form is submitted via POST
    if request.method == "POST":
        # Retrieve form data for email and password
        new_email = request.form.get("email")
        new_password = request.form.get("password")

        # Update email if provided
        if new_email:
            cursor.execute("UPDATE accounts SET email = %s WHERE username = %s", (new_email, username))

        # Update password if provided
        if new_password:
            cursor.execute("UPDATE accounts SET password = %s WHERE username = %s", (new_password, username))

        conn.commit()

        # Redirect to profile page once settings are updated
        return redirect(url_for("profile"))

    # Show settings form with the current email
    return render_template("settings.html", account=account)



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port = 8081)
