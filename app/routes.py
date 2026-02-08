import json

from app import app, db
from app.services.google_books import BookQuery, retrieve_book
from flask import render_template, request, session, redirect, url_for, g
from sqlalchemy.sql import text
from werkzeug.security import check_password_hash, generate_password_hash


@app.route("/")
def index():
    """
    Render the home page.

    Returns:
        Rendered HTML response for the index page.
    """
    return render_template("home.html")


def set_session(user_id):
    """
    Persist the logged-in user id in the session.

    Args:
        user_id: The authenticated user's id.
    """
    session["id"] = user_id


def get_session():
    """
    Retrieve the logged-in user id from the session.

    Returns:
        The user id if present; otherwise None.
    """
    return session.get("id")


def build_initials(username):
    """
    Build a short initials string from the username.
    """
    if not username:
        return "U"
    
    trimmed = username.strip()
    if not trimmed:
        return "U"
    
    parts = [part for part in trimmed.split() if part]
    if not parts:
        return trimmed[0].upper()
    initials = "".join(part[0].upper() for part in parts)

    return initials[:2]


def load_current_user():
    """
    Load the current user for the active session.

    Returns:
        A dict with user data, or None if not authenticated.
    """
    if hasattr(g, "current_user"):
        # Avoid repeated DB lookups in the same request
        return g.current_user
    
    user_id = get_session()
    if user_id is None:
        # No active session means no current user
        g.current_user = None
        return g.current_user
    
    user_row = db.execute(
        text("SELECT id, username FROM users WHERE id = :id"),
        {"id": user_id},
    ).fetchone()
    if not user_row:
        # Session id is stale or user was removed
        g.current_user = None
        return g.current_user
    
    # Store a lightweight user payload for templates
    g.current_user = {
        "id": user_row[0],
        "username": user_row[1],
        "initials": build_initials(user_row[1]),
    }

    return g.current_user


@app.context_processor
def inject_current_user():
    """
    Expose the current user to templates.
    """
    return {"current_user": load_current_user()}


def build_book_context(isbn):
    """
    Build the template context for a book detail page.

    Args:
        isbn: The ISBN string to query.

    Returns:
        A dict of book context values, or None if the book is not found.
    """
    book_row = db.execute(
        text("SELECT title, author, year FROM books WHERE isbn = :isbn"),
        {"isbn": isbn},
    ).fetchone()
    if not book_row:
        # Surface "book not found" to the caller
        return None

    title, author, year = book_row
    # Load local reviews along with reviewer names
    reviews = db.execute(
        text(
            """
            SELECT r.review, r.rating, u.username
            FROM reviews r
            JOIN users u ON r.id = u.id
            WHERE r.isbn = :isbn
            ORDER BY r.created_at DESC
            """
        ),
        {"isbn": isbn},
    ).fetchall()

    # Compute local review stats for the detail view
    localReviewCount = len(reviews)
    localAverageRating = db.execute(
        text("SELECT AVG(rating) FROM reviews WHERE isbn = :isbn"), {"isbn": isbn}
    ).fetchone()[0]

    return {
        "title": title,
        "author": author,
        "year": year,
        "reviews": reviews,
        "localReviewCount": localReviewCount,
        "localAverageRating": localAverageRating,
    }


@app.route("/register", methods=["POST"])
def register():
    """
    Handle user registration.
    
    Reads `username` and `password` from POST form data.
    
    Returns:
        Redirects to sign-in on success or re-renders the index with an error.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # User did not provide a username and/or password
        if username == "" or password == "":
            return render_template(
                "home.html", message="Please enter required fields"
            )

        # Username already exists in database
        userDB = db.execute(
            text("SELECT * FROM users WHERE username = :username"),
            {"username": username},
        ).fetchone()
        if userDB:
            return render_template(
                "home.html",
                message="Username is already taken - please select a different one",
            )

        # Creating new account for the user
        password_hash = generate_password_hash(password)
        db.execute(
            text(
                "INSERT INTO users (username, password) VALUES (:username, :password)"
            ),
            {"username": username, "password": password_hash},
        )
        db.commit()

        return redirect(url_for("signin"))


@app.route("/sign-in", methods=["GET"])
def signin():
    """
    Render the sign-in page.

    Returns:
        Rendered HTML response for the sign-in page.
    """
    return render_template("sign-in.html")


@app.route("/sign-in", methods=["POST"])
def login():
    """
    Authenticate a user and start a session.

    Reads `username` and `password` from POST form data.

    Returns:
        Redirects to search on success or re-renders sign-in with an error.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Username and/or password is missing
        if username == "" or password == "":
            return render_template(
                "sign-in.html", message="Username and/or password is incorrect"
            )

        # Checks if username exists, then validates password hash
        userInfo = db.execute(
            text("SELECT id, password FROM users WHERE username = :username"),
            {"username": username},
        ).fetchone()
        if userInfo and check_password_hash(userInfo[1], password):
            set_session(userInfo[0])  # Remembers user when they sign in
            return redirect(url_for("search"))

        return render_template(
            "sign-in.html", message="Username and/or password is incorrect"
        )


@app.route("/logout", methods=["POST"])
def logout():
    """
    Log out the current user.

    Returns:
        Redirects to the home page.
    """
    if request.method == "POST":
        session.pop("id", None)  # Ends user session
        return redirect(url_for("index"))


@app.route("/profile")
def profile():
    """
    Render the user profile page.

    Returns:
        Rendered HTML response for the profile page.
    """
    current_user = load_current_user()
    if current_user is None:
        # Redirect unauthenticated users back to sign-in
        session.pop("id", None)
        return render_template("sign-in.html", message="Please sign in to view your profile")
    user_id = current_user["id"]

    # Aggregate review count and average rating for the user
    stats = db.execute(
        text("SELECT COUNT(*) AS total, AVG(rating) AS avg_rating FROM reviews WHERE id = :id"),
        {"id": user_id},
    ).fetchone()
    review_total = stats[0] if stats else 0
    average_rating = stats[1] if stats else None

    recent_rows = db.execute(
        text(
            """
            SELECT b.title, b.author, r.rating, r.review, r.created_at
            FROM reviews r
            JOIN books b ON r.isbn = b.isbn
            WHERE r.id = :id
            ORDER BY r.created_at DESC
            LIMIT 5
            """
        ),
        {"id": user_id},
    ).fetchall()

    recent_reviews = []
    for row in recent_rows:
        # Format timestamps for display without requiring a template filter
        created_at = row[4]
        if hasattr(created_at, "strftime"):
            created_label = created_at.strftime("%b %d, %Y")
        elif created_at:
            created_label = str(created_at).split(" ")[0]
        else:
            created_label = ""
        recent_reviews.append(
            {
                "title": row[0],
                "author": row[1],
                "rating": row[2],
                "review": row[3],
                "created_at": created_label,
            }
        )

    return render_template(
        "profile.html",
        review_total=review_total,
        average_rating=average_rating,
        recent_reviews=recent_reviews,
    )


@app.route("/search", methods=["GET", "POST"])
def search():
    """
    Search for books by ISBN, title, or author.

    Reads `isbn`, `title`, and `author` from form data.

    Returns:
        Rendered search results or a validation message.
    """
    if request.method == "POST":
        isbn = request.form["isbn"].strip()
        title = request.form["title"].strip()
        author = request.form["author"].strip()

        # Search by ISBN
        if isbn and title == "" and author == "":
            books = db.execute(
                text("SELECT * FROM books WHERE isbn ILIKE :isbn"),
                {"isbn": f"%{isbn}%"},
            ).fetchall()
            if books:
                return render_template("search.html", books=books)
            else:
                return render_template("search.html", message="No matches were found")

        # Search by book title
        elif title and isbn == "" and author == "":
            books = db.execute(
                text("SELECT * FROM books WHERE title ILIKE :title"),
                {"title": f"%{title}%"},
            ).fetchall()
            if books:
                return render_template("search.html", books=books)
            else:
                return render_template("search.html", message="No matches were found")

        # Search by author
        elif author and isbn == "" and title == "":
            books = db.execute(
                text("SELECT * FROM books WHERE author ILIKE :author"),
                {"author": f"%{author}%"},
            ).fetchall()
            if books:
                return render_template("search.html", books=books)
            else:
                return render_template("search.html", message="No matches were found")

        if not isbn and not title and not author:
            return render_template(
                "search.html", message="Please fill out at least one field below"
            )

        return render_template(
            "search.html", message="Please fill out at most one field below"
        )

    # Returns user to search page
    return render_template("search.html")


@app.route("/return-to-search", methods=["GET", "POST"])
def return_to_search():
    """
    Return the user to the search page.

    Returns:
        Rendered HTML response for the search page.
    """
    return render_template("search.html")


# Extracts information on the user's desired book and outputs it on book page
@app.route("/book", methods=["POST"])
def view():
    """
    Render the book detail page for a selected book.

    Reads `book` (ISBN) from POST form data.

    Returns:
        Rendered book detail page or a validation error.
    """
    # User hits 'View Book' button before completing a search
    try:
        isbn = request.form["book"]
    except KeyError:
        return render_template(
            "search.html",
            message="Please enter a book ISBN, title, or author first",
        )

    # Selecting desired information from 'books' table in database
    context = build_book_context(isbn)
    if not context:
        return render_template("search.html", message="Book not found")

    return render_template(
        "book-detail.html",
        isbn=isbn,
        **context,
    )


@app.route("/review", methods=["POST"])
def review():
    """
    Submit a review for a book.

    Reads `isbn`, `rating`, and `review` from POST form data.

    Returns:
        Rendered book page with errors, or a redirect on success.
    """
    if request.method == "POST":
        id = get_session()
        if id is None:
            return render_template(
                "sign-in.html", message="Please sign in to submit a review"
            )
        isbn = request.form.get("isbn", "").strip()
        review = request.form.get("review", "").strip()
        rating = request.form.get("rating", "").strip()
        if not isbn or not review or not rating:
            if not isbn:
                return render_template(
                    "search.html",
                    message="Please enter a book ISBN, title, or author first",
                )
            context = build_book_context(isbn)
            if not context:
                return render_template("search.html", message="Book not found")
            return render_template(
                "book-detail.html",
                isbn=isbn,
                review_error="Please provide a rating and review",
                **context,
            )

        # User already has existing review for the book
        existingReviewCheck = db.execute(
            text("SELECT review FROM reviews WHERE id = :id AND isbn = :isbn"),
            {"id": id, "isbn": isbn},
        ).fetchone()
        if existingReviewCheck:
            context = build_book_context(isbn)
            if not context:
                return render_template("search.html", message="Book not found")
            return render_template(
                "book-detail.html",
                isbn=isbn,
                review_error=(
                    "Unable to submit review - you have already completed a review for this book"
                ),
                **context,
            )

        # Creating new review
        else:
            db.execute(
                text(
                    "INSERT INTO reviews (id, isbn, rating, review) VALUES (:id, :isbn, :rating, :review)"
                ),
                {"id": id, "isbn": isbn, "rating": rating, "review": review},
            )
            db.commit()

            return redirect(
                url_for(
                    "message",
                    success="Your review has been successfully submitted!",
                )
            )


@app.route("/status")
def message():
    """
    Render a status message page.

    Reads `success` and `error` from query parameters.

    Returns:
        Rendered HTML response for the message page.
    """
    success = request.args.get("success")
    error = request.args.get("error")
    return render_template("status.html", success=success, error=error)


@app.route("/api/books/<isbn>")
def api_info(isbn):
    """
    Render a page with book info from the Google Books API.

    Args:
        isbn: The ISBN string provided in the URL.

    Returns:
        Rendered HTML response with book data or error.
    """
    # Check to see if ISBN exists in database
    checkISBN = db.execute(
        text("SELECT isbn FROM books WHERE isbn = :isbn"), {"isbn": isbn}
    ).fetchone()

    if checkISBN:
        success = retrieve_book(isbn, BookQuery.JSON)
        try:
            book_data = json.loads(success) if success else None
        except (TypeError, json.JSONDecodeError):
            book_data = None

        if book_data and book_data.get("error"):
            return render_template("book-api.html", error=book_data["error"])
        if book_data:
            return render_template("book-api.html", book_data=book_data)
        return render_template("book-api.html", error="Unable to fetch book details")
    else:
        error = "404 Error - The requested URL /api/books/" + isbn + " was not found on this server"
        return render_template("book-api.html", error=error), 404
