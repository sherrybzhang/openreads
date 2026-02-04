# Google Books API Documentation: https://developers.google.com/books/docs/v1/using
import json
import os
import requests

def retrieveBook(isbn, type):
    url = "https://www.googleapis.com/books/v1/volumes?"
    try:
        params = {"q": f"isbn:{isbn}"}
        api_key = os.environ.get("GOOGLE_BOOKS_API_KEY")
        if api_key:
            params["key"] = api_key
        res = requests.get(url, params=params, timeout=10)
    except requests.RequestException:
        return _fallback_response(isbn, type)

    if res.status_code != 200:
        return _fallback_response(isbn, type)

    bookData = res.json()
    items = bookData.get("items") or []
    if not items:
        return _fallback_response(isbn, type)

    volumeInfo = items[0].get("volumeInfo", {})
    authors = volumeInfo.get("authors", [])
    editAuthor = authors if len(authors) > 1 else (authors[0] if authors else "Unknown")

    rating = volumeInfo.get("averageRating", "Unavailable")
    reviewCount = volumeInfo.get("ratingsCount", "0")

    if type == "json":
        bookInfo = {
            "title": volumeInfo.get("title", "Unknown"),
            "author": editAuthor,
            "year": (volumeInfo.get("publishedDate") or "")[:4],
            "isbn": isbn,
            "average_rating": rating,
            "review_count": reviewCount,
        }
        return json.dumps(bookInfo)

    if type == "averageRating":
        return rating

    if type == "numberOfRating":
        return reviewCount

    return _fallback_response(isbn, type)


def _fallback_response(isbn, type):
    if type == "json":
        return json.dumps(
            {
                "error": "Google Books API request failed",
                "isbn": isbn,
                "average_rating": "Unavailable",
                "review_count": "0",
            }
        )
    if type == "averageRating":
        return "Unavailable"
    if type == "numberOfRating":
        return "0"
    return None
