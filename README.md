# OpenReads

OpenReads is a simple book review web application that lets users create accounts, search for books, view book details, and submit reviews. It also supports a JSON-style response via `/api/<isbn>` using the Google Books API.

## Features
- User registration and login
- Search by ISBN, title, or author
- Book detail page with external ratings
- One review per user per book
- API route for book info

## Technologies
- **Languages:** Python, SQL, HTML, CSS
- **Frameworks/Libraries:** Flask, SQLAlchemy, Bootstrap
- **Database:** PostgreSQL
- **API:** Google Books API

## Setup
1) Create and activate a virtual environment.
2) Install dependencies:
```
pip install -r requirements.txt
```
3) Set environment variables (optional defaults are provided in `app/config.py`):
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

## Tests
```
pytest
```

## Formatting
```
./scripts/format.sh
```
