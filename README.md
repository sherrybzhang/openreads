# OpenReads

OpenReads is a book review web application that lets users create accounts, search for books, view book details, and submit reviews. It also supports a JSON-style response via `/api/books/<isbn>` using the Google Books API.

## Features
- User registration and sign in
- Search by ISBN, title, or author
- Book detail page with external ratings
- One review per user per book
- API route for book info

## Technologies
- **Languages:** Python, SQL, HTML, CSS
- **Frameworks/Libraries:** Flask, Flask-Session, SQLAlchemy, Bootstrap
- **Database:** PostgreSQL
- **API:** Google Books API

## Setup
1) Create and activate a virtual environment.
2) Install dependencies:
```
pip install -r requirements.txt
```
3) Set environment variables (optional defaults are provided in `app/config.py` and loaded via `python-dotenv`):
```
export SECRET_KEY="your-secret"
export DATABASE_URL="postgresql://localhost/your_db"
```
4) Create tables:
```
psql -d your_db -f db/schema.sql
```
5) Load sample data (optional):
```
python scripts/import_books.py
```
6) Run the app:
```
python application.py
```
7) Open the app in your browser:
```
http://localhost:8080
```

## Tests
```
pytest
```
