# Google Books API Documentation: https://developers.google.com/books/docs/v1/using
import json
import os
from enum import Enum
from typing import Literal, Optional, overload

import requests


class BookQuery(Enum):
    JSON = "json"
    AVERAGE_RATING = "averageRating"
    NUMBER_OF_RATING = "numberOfRating"


@overload
def retrieveBook(isbn: str, query: Literal[BookQuery.JSON]) -> str: ...

@overload
def retrieveBook(isbn: str, query: Literal[BookQuery.AVERAGE_RATING]) -> str: ...

@overload
def retrieveBook(isbn: str, query: Literal[BookQuery.NUMBER_OF_RATING]) -> str: ...

def retrieveBook(isbn: str, query: BookQuery) -> Optional[str]:
    """
    Retrieve Google Books data for a given ISBN.

    Args:
        isbn: ISBN string to query.
        query: The type of data to return.

    Returns:
        JSON string, rating value, rating count, or None if unavailable.
    """
    url = "https://www.googleapis.com/books/v1/volumes?"
    try:
        # Build request params and include API key if available
        params = {"q": f"isbn:{isbn}"}
        api_key = os.environ.get("GOOGLE_BOOKS_API_KEY")
        if api_key:
            params["key"] = api_key
        res = requests.get(url, params=params, timeout=10)
    except requests.RequestException:
        # Network or request failure: return a safe fallback
        return _fallback_response(isbn, query)

    if res.status_code != 200:
        # Non-OK status: return a safe fallback
        return _fallback_response(isbn, query)

    bookData = res.json()
    items = bookData.get("items") or []
    if not items:
        # No results: return a safe fallback
        return _fallback_response(isbn, query)

    volumeInfo = items[0].get("volumeInfo", {})
    authors = volumeInfo.get("authors", [])
    editAuthor = authors if len(authors) > 1 else (authors[0] if authors else "Unknown")

    rating = volumeInfo.get("averageRating", "Unavailable")
    reviewCount = volumeInfo.get("ratingsCount", "0")

    if query == BookQuery.JSON:
        # Return a compact JSON string for API route usage
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
        # Return average rating as provided by Google Books
        return rating

    if query == BookQuery.NUMBER_OF_RATING:
        # Return ratings count as provided by Google Books
        return reviewCount

    # Unknown query type: fall back safely
    return _fallback_response(isbn, query)


@overload
def _fallback_response(isbn: str, query: Literal[BookQuery.JSON]) -> str: ...

@overload
def _fallback_response(isbn: str, query: Literal[BookQuery.AVERAGE_RATING]) -> str: ...

@overload
def _fallback_response(isbn: str, query: Literal[BookQuery.NUMBER_OF_RATING]) -> str: ...

def _fallback_response(isbn: str, query: BookQuery) -> Optional[str]:
    """
    Return a safe fallback response when API data is unavailable.

    Args:
        isbn: ISBN string used for context in the fallback payload.
        query: The type of data requested.

    Returns:
        JSON string, rating value, rating count, or None when unsupported.
    """
    if query == BookQuery.JSON:
        # Provide a minimal JSON payload on failure
        return json.dumps(
            {
                "error": "Google Books API request failed",
                "isbn": isbn,
                "average_rating": "Unavailable",
                "review_count": "0",
            }
        )
    if query == BookQuery.AVERAGE_RATING:
        # Match the rating return type on failure
        return "Unavailable"
    if query == BookQuery.NUMBER_OF_RATING:
        # Match the ratings count return type on failure
        return "0"
    return None
