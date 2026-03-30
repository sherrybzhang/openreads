import json
from typing import Optional, TypedDict

from app import app, db
from app.services.google_books import BookQuery, retrieve_book
from flask import render_template, request, session, redirect, url_for, g
from flask.typing import ResponseReturnValue
from sqlalchemy.sql import text
from werkzeug.security import check_password_hash, generate_password_hash


class CurrentUser(TypedDict):
    id: int
    username: str
    initials: str


BookContext = dict[str, object]
FieldErrors = dict[str, str]


def _render_home_page(
    message: Optional[str] = None,
    form_data: Optional[dict[str, str]] = None,
    field_errors: Optional[FieldErrors] = None,
) -> str:
    """
    Render the home page with optional form state.
    """
    return render_template(
        "home.html",
        page_title="OpenReads | Create Account",
        message=message,
        form_data=form_data or {},
        field_errors=field_errors or {},
    )


def _render_sign_in_page(
    message: Optional[str] = None,
    form_data: Optional[dict[str, str]] = None,
    field_errors: Optional[FieldErrors] = None,
) -> str:
    """
    Render the sign-in page with optional form state.
    """
    return render_template(
        "sign-in.html",
        page_title="OpenReads | Sign In",
        message=message,
        form_data=form_data or {},
        field_errors=field_errors or {},
    )


def _render_search_page(
    *,
    message: Optional[str] = None,
    books: Optional[list[object]] = None,
    form_data: Optional[dict[str, str]] = None,
) -> str:
    """
    Render the search page with optional search results and form state.
    """
    return render_template(
        "search.html",
        page_title="OpenReads | Search Books",
        message=message,
        books=books or [],
        form_data=form_data or {"isbn": "", "title": "", "author": ""},
    )


@app.route("/")
def index() -> str:
    """
    Render the home page.

    Returns:
        Rendered HTML response for the index page.
    """
    return _render_home_page()


def _set_session(user_id: int) -> None:
    """
    Persist the logged-in user id in the session.

    Args:
        user_id: The authenticated user's id.
    """
    session["id"] = user_id


def _get_session() -> Optional[int]:
    """
    Retrieve the logged-in user id from the session.

    Returns:
        The user id if present; otherwise None.
    """
    return session.get("id")


def _build_initials(username: Optional[str]) -> str:
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


def _load_current_user() -> Optional[CurrentUser]:
    """
    Load the current user for the active session.

    Returns:
        A dict with user data, or None if not authenticated.
    """
    if hasattr(g, "current_user"):
        # Avoid repeated DB lookups in the same request
        return g.current_user
    
    user_id = _get_session()
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
        "initials": _build_initials(user_row[1]),
    }

    return g.current_user


@app.context_processor
def _inject_current_user() -> dict[str, Optional[CurrentUser]]:
    """
    Expose the current user to templates.
    """
    return {"current_user": _load_current_user()}


def _build_book_context(isbn: str) -> Optional[BookContext]:
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
    local_review_count = len(reviews)
    local_average_rating = db.execute(
        text("SELECT AVG(rating) FROM reviews WHERE isbn = :isbn"), {"isbn": isbn}
    ).fetchone()[0]

    return {
        "title": title,
        "author": author,
        "year": year,
        "reviews": reviews,
        "local_review_count": local_review_count,
        "local_average_rating": local_average_rating,
    }


@app.route("/register", methods=["POST"])
def register() -> ResponseReturnValue:
    """
    Handle user registration.
    
    Reads `username` and `password` from POST form data.
    
    Returns:
        Redirects to sign-in on success or re-renders the index with an error.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        form_data = {"username": username}

        # User did not provide a username and/or password
        field_errors: FieldErrors = {}
        if username == "":
            field_errors["username"] = "Please enter a username."
        if password == "":
            field_errors["password"] = "Please enter a password."
        if field_errors:
            return _render_home_page(
                form_data=form_data,
                field_errors=field_errors,
            )

        # Username already exists in database
        user_db = db.execute(
            text("SELECT * FROM users WHERE username = :username"),
            {"username": username},
        ).fetchone()
        if user_db:
            return _render_home_page(
                form_data=form_data,
                field_errors={
                    "username": (
                        "Username is already taken. Please select a different one."
                    )
                },
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

        return redirect(url_for("sign_in"))


@app.route("/sign-in", methods=["GET"])
def sign_in() -> str:
    """
    Render the sign-in page.

    Returns:
        Rendered HTML response for the sign-in page.
    """
    return _render_sign_in_page()


@app.route("/sign-in", methods=["POST"])
def login() -> ResponseReturnValue:
    """
    Authenticate a user and start a session.

    Reads `username` and `password` from POST form data.

    Returns:
        Redirects to search on success or re-renders sign-in with an error.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        form_data = {"username": username}

        # Username and/or password is missing
        field_errors = {}
        if username == "":
            field_errors["username"] = "Please enter your username."
        if password == "":
            field_errors["password"] = "Please enter your password."
        if field_errors:
            return _render_sign_in_page(
                form_data=form_data,
                field_errors=field_errors,
            )

        # Checks if username exists, then validates password hash
        user_info = db.execute(
            text("SELECT id, password FROM users WHERE username = :username"),
            {"username": username},
        ).fetchone()
        if user_info and check_password_hash(user_info[1], password):
            _set_session(user_info[0])  # Remembers user when they sign in
            return redirect(url_for("search"))

        return _render_sign_in_page(
            form_data=form_data,
            field_errors={"password": "Username and/or password is incorrect."},
        )


@app.route("/logout", methods=["POST"])
def logout() -> ResponseReturnValue:
    """
    Log out the current user.

    Returns:
        Redirects to the home page.
    """
    if request.method == "POST":
        session.pop("id", None)  # Ends user session
        return redirect(url_for("index"))


@app.route("/profile")
def profile() -> str:
    """
    Render the user profile page.

    Returns:
        Rendered HTML response for the profile page.
    """
    current_user = _load_current_user()
    if current_user is None:
        # Redirect unauthenticated users back to sign-in
        session.pop("id", None)
        return _render_sign_in_page(message="Please sign in to view your profile.")
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
        page_title=f"OpenReads | {current_user['username']}",
        review_total=review_total,
        average_rating=average_rating,
        recent_reviews=recent_reviews,
    )


@app.route("/search", methods=["GET", "POST"])
def search() -> str:
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
        form_data = {"isbn": isbn, "title": title, "author": author}

        # Search by ISBN
        if isbn and title == "" and author == "":
            books = db.execute(
                text("SELECT * FROM books WHERE isbn ILIKE :isbn"),
                {"isbn": f"%{isbn}%"},
            ).fetchall()
            if books:
                return _render_search_page(books=books, form_data=form_data)
            else:
                return _render_search_page(
                    message="No matches were found.",
                    form_data=form_data,
                )

        # Search by book title
        elif title and isbn == "" and author == "":
            books = db.execute(
                text("SELECT * FROM books WHERE title ILIKE :title"),
                {"title": f"%{title}%"},
            ).fetchall()
            if books:
                return _render_search_page(books=books, form_data=form_data)
            else:
                return _render_search_page(
                    message="No matches were found.",
                    form_data=form_data,
                )

        # Search by author
        elif author and isbn == "" and title == "":
            books = db.execute(
                text("SELECT * FROM books WHERE author ILIKE :author"),
                {"author": f"%{author}%"},
            ).fetchall()
            if books:
                return _render_search_page(books=books, form_data=form_data)
            else:
                return _render_search_page(
                    message="No matches were found.",
                    form_data=form_data,
                )

        if not isbn and not title and not author:
            return _render_search_page(
                message="Please fill out at least one field below.",
                form_data=form_data,
            )

        return _render_search_page(
            message="Please fill out at most one field below.",
            form_data=form_data,
        )

    # Returns user to search page
    return _render_search_page()


@app.route("/return-to-search", methods=["GET", "POST"])
def return_to_search() -> str:
    """
    Return the user to the search page.

    Returns:
        Rendered HTML response for the search page.
    """
    return _render_search_page()


# Extracts information on the user's desired book and outputs it on book page
@app.route("/book", methods=["POST"])
def view() -> str:
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
        return _render_search_page(
            message="Please enter a book ISBN, title, or author first.",
        )

    # Selecting desired information from 'books' table in database
    context = _build_book_context(isbn)
    if not context:
        return _render_search_page(message="Book not found.")

    return render_template(
        "book-detail.html",
        page_title=f"OpenReads | {context['title']}",
        isbn=isbn,
        review_text="",
        selected_rating="",
        **context,
    )


@app.route("/review", methods=["POST"])
def review() -> ResponseReturnValue:
    """
    Submit a review for a book.

    Reads `isbn`, `rating`, and `review` from POST form data.

    Returns:
        Rendered book page with errors, or a redirect on success.
    """
    if request.method == "POST":
        user_id = _get_session()
        if user_id is None:
            return _render_sign_in_page(message="Please sign in to submit a review.")
        isbn = request.form.get("isbn", "").strip()
        review = request.form.get("review", "").strip()
        rating = request.form.get("rating", "").strip()
        if not isbn or not review or not rating:
            if not isbn:
                return _render_search_page(
                    message="Please enter a book ISBN, title, or author first.",
                )
            context = _build_book_context(isbn)
            if not context:
                return _render_search_page(message="Book not found.")
            return render_template(
                "book-detail.html",
                page_title=f"OpenReads | {context['title']}",
                isbn=isbn,
                review_error="Please provide a rating and review.",
                review_text=review,
                selected_rating=rating,
                **context,
            )

        # User already has existing review for the book
        existing_review_check = db.execute(
            text("SELECT review FROM reviews WHERE id = :id AND isbn = :isbn"),
            {"id": user_id, "isbn": isbn},
        ).fetchone()
        if existing_review_check:
            context = _build_book_context(isbn)
            if not context:
                return _render_search_page(message="Book not found.")
            return render_template(
                "book-detail.html",
                page_title=f"OpenReads | {context['title']}",
                isbn=isbn,
                review_error=(
                    "Unable to submit review. You have already completed a review for this book."
                ),
                review_text=review,
                selected_rating=rating,
                **context,
            )

        # Creating new review
        else:
            db.execute(
                text(
                    "INSERT INTO reviews (id, isbn, rating, review) VALUES (:id, :isbn, :rating, :review)"
                ),
                {"id": user_id, "isbn": isbn, "rating": rating, "review": review},
            )
            db.commit()

            return redirect(
                url_for(
                    "message",
                    success="Your review has been successfully submitted!",
                )
            )


@app.route("/status")
def message() -> str:
    """
    Render a status message page.

    Reads `success` and `error` from query parameters.

    Returns:
        Rendered HTML response for the message page.
    """
    success = request.args.get("success")
    error = request.args.get("error")
    return render_template(
        "status.html",
        page_title="OpenReads | Status",
        success=success,
        error=error,
    )


@app.route("/api/books/<isbn>")
def api_info(isbn: str) -> ResponseReturnValue:
    """
    Render a page with book info from the Google Books API.

    Args:
        isbn: The ISBN string provided in the URL.

    Returns:
        Rendered HTML response with book data or error.
    """
    # Check to see if ISBN exists in database
    check_isbn = db.execute(
        text("SELECT isbn FROM books WHERE isbn = :isbn"), {"isbn": isbn}
    ).fetchone()

    if check_isbn:
        success = retrieve_book(isbn, BookQuery.JSON)
        try:
            book_data = json.loads(success) if success else None
        except (TypeError, json.JSONDecodeError):
            book_data = None

        if book_data and book_data.get("error"):
            return render_template(
                "book-api.html",
                page_title=f"OpenReads | API | {isbn}",
                error=book_data["error"],
            )
        if book_data:
            return render_template(
                "book-api.html",
                page_title=f"OpenReads | API | {isbn}",
                book_data=book_data,
            )
        return render_template(
            "book-api.html",
            page_title=f"OpenReads | API | {isbn}",
            error="Unable to fetch book details.",
        )
    else:
        error = "404 Error - The requested URL /api/books/" + isbn + " was not found on this server."
        return render_template(
            "book-api.html",
            page_title=f"OpenReads | API | {isbn}",
            error=error,
        ), 404
