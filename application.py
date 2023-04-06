from googlebooksAPI import retrieveBook
from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text
from sqlalchemy import create_engine

app = Flask(__name__)
app.secret_key = '_23hd9udhf*HUHDF'

# Configures session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Sets up database
engine = create_engine("postgresql://localhost/sherryzhang")
db = scoped_session(sessionmaker(bind=engine))

# Routes to home page
@app.route("/")
def index():
    return render_template("index.html")

# Sets up session
@app.route('/set_session')
def set_session(id):
    session['id'] = id

@app.route("/get_session")
def get_session():
    return session.get('id')

# Handles user registrations
@app.route("/register", methods=["POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # User did not provide a username and/or password
        if username == "" or password == "":
            return render_template("index.html", message="* Please enter required fields.")
        
        # Username already exists in database
        userDB = db.execute(text("SELECT * FROM users WHERE username = :username"), 
            {"username": username}).fetchone()
        if userDB:
            return render_template("index.html", message="* Username is already taken. Please select a different one.")
        
        # Creating new account for the user
        db.execute(text("INSERT INTO users (username, password) VALUES (:username, :password)"), 
            {"username": username, "password": password})   
        db.commit()

        return render_template("login.html")

# LOGIN option on home page that routes to login page. Used by users that already have an account
@app.route("/login", methods=["POST"])
def signin():
    if request.method == "POST":
        return render_template("login.html")

# Logs in the user, begins user session, and redirects to search page
@app.route("/signin", methods=["POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Username and/or password is missing
        if username == "" or password == "":
            render_template("login.html", message = "* Username and/or password is incorrect.")
        
        # Checks if username/password exists in database and if it matches the user's inputs
        userInfo = db.execute(text("SELECT * FROM users WHERE username = :username AND password = :password"), 
            {"username": username, "password": password}).fetchone()
        if username != "" and password != "":
            id = db.execute(text("SELECT id FROM users WHERE username = :username"), 
                {"username": username}).fetchone()[0]
            set_session(id) # Remembers user when they log in
        if userInfo:
            return render_template("search.html")
        
        return render_template("login.html", message = "* Username and/or password is incorrect.")

# Logs user out and ends session
@app.route("/logout", methods=["POST"])
def logout():
    if request.method == "POST":
        session.pop("id", None) # Ends user session
        return render_template("index.html")

# Performs book search
@app.route("/search", methods=["POST"])
def search():
    if request.method == "POST":
        isbn = request.form["isbn"]
        title= request.form["title"]
        author = request.form["author"]
        
        # Search by ISBN
        if isbn and title == "" and author == "":
            books = db.execute(text("SELECT * FROM books WHERE isbn LIKE :isbn"), 
                {"isbn": isbn+"%"}).fetchall()
            if books: 
                return render_template("search.html", books=books)
            else:
                return render_template("search.html", message="*No matches were found.")
        
        # Search by Book Title
        elif title and isbn == "" and author == "":
            books = db.execute(text("SELECT * FROM books WHERE title LIKE :title"), 
                {"title": title+"%"}).fetchall()
            if books: 
                return render_template("search.html", books=books)
            else:
                return render_template("search.html", message="*No matches were found.")
        
        # Search by Author
        elif author and isbn == "" and title == "":
            books = db.execute(text("SELECT * FROM books WHERE author LIKE :author"), 
                {"author": author+"%"}).fetchall()
            if books: 
                return render_template("search.html", books=books)
            else:
                return render_template("search.html", message="*No matches were found.")
            
        else:
            return render_template("search.html", message="* Please fill out at most one field below")

# Returns user to search page
@app.route("/returnToSearch", methods=["POST"])
def returntoSearch():
    if request.method == "POST":
        return render_template("search.html")

# Extracts information on the user's desired book and outputs it on book page
@app.route("/view", methods=["POST"])
def view():
    if request.method == "POST":
        # User hits 'View Book' button before completing a search
        try:
            isbn = request.form["book"]
        except KeyError:
            return render_template("search.html", message="* Please enter a book ISBN, title, or author first.")
        
        # Selecting desired information from 'books' table in database
        title = db.execute(text("SELECT title FROM books WHERE isbn = :isbn"),
            {"isbn": isbn}).fetchone()[0]
        author = db.execute(text("SELECT author FROM books WHERE isbn = :isbn"),
            {"isbn": isbn}).fetchone()[0]
        year = db.execute(text("SELECT year FROM books WHERE isbn = :isbn"),
            {"isbn": isbn}).fetchone()[0]
        averageRating = retrieveBook(isbn, "averageRating")
        numberOfRating = retrieveBook(isbn, "numberOfRating")
        reviews = db.execute(text("SELECT * FROM reviews WHERE isbn = :isbn"),
            {"isbn": isbn}).fetchall()

        return render_template("book.html", isbn=isbn, title=title, author=author, year=year, averageRating=averageRating, numberOfRating=numberOfRating, reviews=reviews)

# Submits user's book review
@app.route("/review", methods=["POST"])
def review():
    if request.method == "POST":
        id = get_session()
        isbn = request.form["isbn"]     
        review = request.form["review"]
        rating = request.form["rating"]

        # User already has existing review for the book
        existingReviewCheck = db.execute(text("SELECT review FROM reviews WHERE id = :id AND isbn = :isbn"),
            {"id": id, "isbn": isbn}).fetchone()
        if existingReviewCheck:
            return render_template("error.html", error="Unable to submit review. You have already completed a review for this book.")
        
        # Creating new review
        else:
            db.execute(text("INSERT INTO reviews (id, isbn, rating, review) VALUES (:id, :isbn, :rating, :review)"),
                {"id": id, "isbn": isbn, "rating": rating, "review": review}) 
            db.commit()

            return render_template("success.html", success="Your review has been successfully submitted!")

# Redirects user to a new page containing book information pulled from Google Books API
@app.route("/api/<isbn>")
def apiInfo(isbn):
    # Check to see if ISBN exists in database
    checkISBN = db.execute(text("SELECT isbn FROM books WHERE isbn = :isbn"),
        {"isbn": isbn}).fetchone()
    
    if checkISBN:
        success = retrieveBook(isbn,"json")
        return render_template("api.html", success=success)
    else:
        error = "404 Error. The requested URL /api/" + isbn + " was not found on this server." 
        return render_template("api.html", error=error)

if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0", port=8080)