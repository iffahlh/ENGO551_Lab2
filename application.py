import os

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
import requests

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))

@app.route("/")
def index():
    session['logged_in'] = session.get('logged_in', 'False')
    if session['logged_in']==True:
        return render_template("search.html", search=True)
    else:
        return render_template("search.html", search=False)

@app.route("/register", methods=["GET", "POST"])
def register():
    with engine.connect() as db:
        if request.method == "POST":
            name = request.form.get('name')
            user = request.form.get('username')
            pwd = request.form.get('password')
            if name is None or user is None or pwd is None:
                message="Missing field(s)"  
                return render_template("register.html", message=message) 
            if db.execute("SELECT * FROM users WHERE username = %(username)s", {"username": user}).rowcount != 0:
                message="Error: Username already exists."  
                return render_template("register.html", message=message) 
            elif name and user and pwd:
                db.execute("INSERT INTO users (name, username, password) VALUES (%(name)s, %(username)s, %(password)s)", {"name": name, "username": user, "password": pwd })   
                session['logged_in'] = True
                session['username'] = user 
                return render_template("register_success.html")                  
        else:
            return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    with engine.connect() as db:
        if request.method == "POST":
            user = request.form.get('username')
            pwd = request.form.get('password')
            query_user = db.execute("SELECT * FROM users WHERE username = %(username)s AND password = %(password)s", {"username": user, "password": pwd }).fetchone()       
            if query_user[1] == user and query_user[2] == pwd:
                session['logged_in'] = True
                session['username'] = user       
                return redirect(url_for("search"))
            else:
                message="Incorrect username or password"
                return render_template("login.html", message=message)   
            
        else:
            return render_template("login.html")

@app.route("/logout")
def logout():
    session['logged_in']= False
    session['username']=None
    message="You've been logged out"
    return render_template("login.html", message=message, search=False)
        
@app.route("/search", methods=['GET', 'POST'])
def search():
    with engine.connect() as db:
        session['logged_in'] = session.get('logged_in', 'False')
        if session['logged_in'] == True:
            if request.method == "POST":
                query = "%{}%".format(request.form.get('query'))
                results = db.execute("SELECT * FROM books WHERE isbn LIKE %(isbn)s OR UPPER(title) LIKE UPPER(%(title)s) OR UPPER(author) LIKE UPPER(%(author)s) LIMIT 20", {"isbn": query, "title": query, "author": query }).fetchall()
                return render_template("search.html", search=True, results=results, query=query[1:-1])
            else:
                return render_template("search.html", search=True)
        else:
            return render_template("search.html", search=False)

@app.route("/result/<isbn>", methods=["GET", "POST"])
def result(isbn):
    with engine.connect() as db:
        session['logged_in'] = session.get('logged_in', 'False')
        session['username'] = session.get('username', None)
        book_result = db.execute("SELECT * FROM books WHERE isbn = %(isbn)s", {"isbn": isbn}).fetchall()
        book_reviews = db.execute("SELECT username, rating, comment FROM review WHERE isbn = %(isbn)s", {"isbn": isbn}).fetchall()
        reviews=""
        if session['logged_in'] == True:
            if request.method == "GET":
                if db.execute("SELECT * FROM books WHERE isbn = %(isbn)s", {"isbn": isbn}).rowcount != 0:
                    message=isbn
                    value=getGoogleRating(isbn)
                    if book_reviews == []:
                        reviews = "There are no reviews yet."
                    else:
                        reviews=""
                    return render_template("result.html", search=True, message=message, book_result=book_result, reviews=reviews, book_reviews=book_reviews, value=value)
                else:
                    return render_template('404.html'), 404
            if request.method == "POST":
                username=session['username']
                user_review = db.execute("SELECT * FROM review WHERE isbn = %(isbn)s AND username = %(username)s", {"isbn": isbn, "username": username}).rowcount
                rating=request.form.get('rating')
                comment=request.form.get('comment')
                value=getGoogleRating(isbn)
                if user_review==0:
                    db.execute("INSERT INTO review (username, rating, comment, isbn) VALUES (%(username)s, %(rating)s, %(comment)s,  %(isbn)s)", {"username": username, "rating": rating,"comment": comment, "isbn": isbn,})
                    book_reviews = db.execute("SELECT username, rating, comment FROM review WHERE isbn = %(isbn)s", {"isbn": isbn}).fetchall()
                    submitted="Your review has been submitted"
                else:
                    submitted="You've already submitted a review!"
                return render_template("result.html", search=True,submitted=submitted, book_result=book_result, reviews=reviews, book_reviews=book_reviews, value=value)
        else:
            message = "Unauthorized!"
            return render_template("result.html", search=False, message=message)            

def getAPIdict(isbn):
    req=requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": "isbn:{}".format(isbn)})
    return req

def getGoogleRating(isbn):
    req=getAPIdict(isbn)
    avg_rating = req.json()['items'][0]['volumeInfo'].get('averageRating',0)
    return avg_rating

@app.route("/api/<isbn>", methods=['GET'])
def api(isbn):
    
    with engine.connect() as db:
        if db.execute("SELECT * FROM books WHERE isbn = %(isbn)s", {"isbn": isbn}).rowcount != 0:
            req=getAPIdict(isbn).json()['items'][0]['volumeInfo']
            isbn=req.get('industryIdentifiers', None)
            isbn_10=None
            isbn_13=None
            if isbn:
                for i in isbn:
                    if i['type'] == 'ISBN_10':
                        isbn_10=i['identifier']
                    elif i['type'] == 'ISBN_13':
                        isbn_13=i['identifier']

            json_response={
                'title': req.get('title', None),
                'author': req.get('title', None),
                'date': req.get('publishedDate', None),
                'num_review': req.get('ratingsCount', None),
                'avg_rating': req.get('averageRating', None),
                'isbn_10': isbn_10,
                'isbn_13': isbn_13
            }
            
            return jsonify(json_response)
        else:
            return render_template('404.html'), 404

@app.errorhandler(404)
def page_not_found(e):
   return render_template('404.html'), 404

