# Google Books API Documentation: https://developers.google.com/books/docs/v1/using
import json
import os
from enum import Enum

import requests


class BookQuery(Enum):
    JSON = "json"
    AVERAGE_RATING = "averageRating"
    NUMBER_OF_RATING = "numberOfRating"

def retrieveBook(isbn, query: BookQuery):
    url = "https://www.googleapis.com/books/v1/volumes?"
    try:
        params = {"q": f"isbn:{isbn}"}
        api_key = os.environ.get("GOOGLE_BOOKS_API_KEY")
        if api_key:
            params["key"] = api_key
        res = requests.get(url, params=params, timeout=10)
    except requests.RequestException:
        return _fallback_response(isbn, query)

    if res.status_code != 200:
        return _fallback_response(isbn, query)

    bookData = res.json()
    items = bookData.get("items") or []
    if not items:
        return _fallback_response(isbn, query)

    volumeInfo = items[0].get("volumeInfo", {})
    authors = volumeInfo.get("authors", [])
    editAuthor = authors if len(authors) > 1 else (authors[0] if authors else "Unknown")

    rating = volumeInfo.get("averageRating", "Unavailable")
    reviewCount = volumeInfo.get("ratingsCount", "0")

    if query == BookQuery.JSON:
        bookInfo = {
            "title": volumeInfo.get("title", "Unknown"),
            "author": editAuthor,
            "year": (volumeInfo.get("publishedDate") or "")[:4],
            "isbn": isbn,
            "average_rating": rating,
            "review_count": reviewCount,
        }
        return json.dumps(bookInfo)

    if query == BookQuery.AVERAGE_RATING:
        return rating

    if query == BookQuery.NUMBER_OF_RATING:
        return reviewCount

    return _fallback_response(isbn, query)


def _fallback_response(isbn, query: BookQuery):
    if query == BookQuery.JSON:
        return json.dumps(
            {
                "error": "Google Books API request failed",
                "isbn": isbn,
                "average_rating": "Unavailable",
                "review_count": "0",
            }
        )
    if query == BookQuery.AVERAGE_RATING:
        return "Unavailable"
    if query == BookQuery.NUMBER_OF_RATING:
        return "0"
    return None
