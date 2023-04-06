# Nittany Reads

*February 2023 - March 2023*

Nittany Reads—a book review platform—is a simple web application that allows users to create an account, search for books, view book details, and write reviews. Below is a breakdown of my project.

## Tools

**Languages**: *Python, SQL, HTML, CSS*

**Framework/Libraries**: *Flask, SQLAlchemy, Bootstrap*

**Database**: *PostgreSQL*

**API**: *Google Books API*

## File Descriptions

### Python

**application.py:** *The application’s root. Imports Flask and other necessary modules. Creates and configures the Flask application. Configures database. Starts the server by running the Flask application instance. Handles incoming requests from users and returns responses.*

**googlebooksAPI.py:** *If users make a GET request to the website’s /api/isbn route, where isbn is a book’s ISBN, the website returns a JSON response containing the book’s title, author, publication date, ISBN, average rating, and number of ratings. On the book page, the API is used to extract and display information on a book’s average rating and number of ratings.*

**import.py:** *Reads and takes the books from books.csv and imports them into the PostgreSQL database.*

### CSV

**books.csv:** *Spreadsheet in CSV format containing 5000 different books. Each book has an ISBN, a title, an author, and a publication year.*

### SQL

**queries.sql:** Contains SQL queries used for creating the tables (users, books, reviews) in the database.  

### HTML

**api.html:** *Page where /api/isbn routes to. Showcases the JSON object, which contains information on the book’s title, author, publication year, ISBN, average rating, and number of ratings.*

**base.html:** *Layout template that contains the common HTML elements shared across multiple web pages in the application. Reduces the duplication of code and makes it easier to maintain and update the application while providing a consistent user experience across all pages.*

**book.html:** *Displays the details of the user’s desired book, including ISBN, title, author, publication year, average rating, and the number of ratings, and provides users an area to submit their book reviews.*

**index.html:** *Home page of the application. Welcomes the users to the website and provides the option to register an account or log in if they are returning users.*

**login.html:** *Login page where users can log into their accounts.*

**message.html:** *Informs the user whether or not his or her review has been successfully submitted.*

**search.html:** *Provides users with three different ways to search for a book. Users can search for a book by ISBN, title, or author. After a search, a list of results will appear in the drop-down list where users can select and view details of their desired book.*

### CSS

**style.css:** *Contains the presentation and style for the HTML files of the application.*

## Notes

This project was for my CMPSC 297: Hands-on Web Development class. Originally, the project was in a repository under the CMPSC 297 organization. However, after I submitted my project, I returned to it, revamped it, discovered and resolved leftover bugs, and transferred the updated version onto my personal public repository nittanyreads. 
