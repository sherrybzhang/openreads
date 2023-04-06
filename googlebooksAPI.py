# Google Books API Documentation: https://developers.google.com/books/docs/v1/using 

import requests
import json

def retrieveBook(isbn, type):
    url = "https://www.googleapis.com/books/v1/volumes?"
    res = requests.get(url, 
                   params={ "q": {isbn} })
    if res.status_code != 200:
        raise Exception("ERROR: API request unsuccessful.")

    bookData = res.json()
    volumeInfo = bookData["items"][0]["volumeInfo"]
    author = volumeInfo["authors"]
    editAuthor = author if len(author) > 1 else author[0]

    # Checking if rating exists for the book
    try: 
        rating = volumeInfo["averageRating"]
        reviewCount = volumeInfo["ratingsCount"]
    except KeyError:
        rating = "Unavailable"
        reviewCount = 0
    
    # Returns complete book information as JSON object
    if type == "json":
        # Creating dictionary, which will return as JSON object
        bookInfo = {
        "title": volumeInfo['title'],
        "author": editAuthor,
        "year": volumeInfo['publishedDate'][0:4],
        "isbn": isbn,
        "average_rating": rating,
        "review_count": reviewCount
        }
        return json.dumps(bookInfo)
    
    # Returns book's average rating
    elif type == "averageRating":
        return rating
    
    # Returns number of ratings for the book
    elif type == "numberOfRating":
        return reviewCount