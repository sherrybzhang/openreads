# Google Books API Documentation: https://developers.google.com/books/docs/v1/using
import json
import os
import logging
import requests

from enum import Enum
from typing import Literal, Optional, overload


_logger = logging.getLogger(__name__)


def _normalize_isbn(isbn: str) -> str:
    """
    Normalize ISBN by stripping spaces and hyphens.
    """
    return isbn.replace("-", "").replace(" ", "")


def _is_valid_isbn(isbn: str) -> bool:
    """
    Return True if ISBN looks like a 10 or 13 character ISBN.
    """
    normalized = _normalize_isbn(isbn)
    if len(normalized) == 10:
        return normalized[:-1].isdigit() and (
            normalized[-1].isdigit() or normalized[-1].upper() == "X"
        )
    if len(normalized) == 13:
        return normalized.isdigit()
    
    return False


class BookQuery(Enum):
    JSON = "json"
    AVERAGE_RATING = "averageRating"
    NUMBER_OF_RATING = "numberOfRating"


@overload
def retrieve_book(isbn: str, query: Literal[BookQuery.JSON]) -> str: ...

@overload
def retrieve_book(isbn: str, query: Literal[BookQuery.AVERAGE_RATING]) -> Optional[float]: ...

@overload
def retrieve_book(isbn: str, query: Literal[BookQuery.NUMBER_OF_RATING]) -> int: ...

def retrieve_book(isbn: str, query: BookQuery) -> Optional[object]:
    """
    Retrieve Google Books data for a given ISBN.

    Args:
        isbn: ISBN string to query.
        query: The type of data to return.

    Returns:
        JSON string, rating value (float or None), rating count (int), or None if unavailable.
    """
    if not _is_valid_isbn(isbn):
        _logger.warning("Invalid ISBN provided: %s", isbn)
        return _fallback_response(isbn, query)

    url = "https://www.googleapis.com/books/v1/volumes?"
    try:
        # Build request params and include API key if available
        normalized_isbn = _normalize_isbn(isbn)
        params = {"q": f"isbn:{normalized_isbn}"}
        api_key = os.environ.get("GOOGLE_BOOKS_API_KEY")
        if api_key:
            params["key"] = api_key
        res = requests.get(url, params=params, timeout=10)
    except requests.RequestException as exc:
        _logger.warning("Google Books request failed for ISBN %s: %s", isbn, exc)
        # Network or request failure: return a safe fallback
        return _fallback_response(isbn, query)

    if res.status_code != 200:
        _logger.warning(
            "Google Books non-200 response for ISBN %s: %s", isbn, res.status_code
        )
        # Non-OK status: return a safe fallback
        return _fallback_response(isbn, query)

    book_data = res.json()
    items = book_data.get("items") or []
    if not items:
        _logger.info("Google Books returned no items for ISBN %s", isbn)
        # No results: return a safe fallback
        return _fallback_response(isbn, query)

    volume_info = items[0].get("volumeInfo", {})
    authors = volume_info.get("authors", [])
    display_author = authors if len(authors) > 1 else (authors[0] if authors else "Unknown")

    rating_raw = volume_info.get("averageRating")
    rating = float(rating_raw) if rating_raw is not None else None
    review_count = volume_info.get("ratingsCount", 0)

    if query == BookQuery.JSON:
        # Return a compact JSON string for API route usage
        book_info = {
            "title": volume_info.get("title", "Unknown"),
            "author": display_author,
            "year": (volume_info.get("publishedDate") or "")[:4],
            "isbn": isbn,
            "average_rating": rating,
            "review_count": review_count,
        }
        return json.dumps(book_info)

    if query == BookQuery.AVERAGE_RATING:
        # Return average rating as provided by Google Books
        return rating

    if query == BookQuery.NUMBER_OF_RATING:
        # Return ratings count as provided by Google Books
        return review_count

    # Unknown query type: fall back safely
    return _fallback_response(isbn, query)


@overload
def _fallback_response(isbn: str, query: Literal[BookQuery.JSON]) -> str: ...

@overload
def _fallback_response(isbn: str, query: Literal[BookQuery.AVERAGE_RATING]) -> str: ...

@overload
def _fallback_response(isbn: str, query: Literal[BookQuery.NUMBER_OF_RATING]) -> str: ...

def _fallback_response(isbn: str, query: BookQuery) -> Optional[object]:
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
                "review_count": 0,
            }
        )
    if query == BookQuery.AVERAGE_RATING:
        # Match the rating return type on failure
        return None
    if query == BookQuery.NUMBER_OF_RATING:
        # Match the ratings count return type on failure
        return 0
    
    return None
