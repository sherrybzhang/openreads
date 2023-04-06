# Nittany Reads

*February 2023 - April 2023*

Nittany Reads—a book review platform—is a simple web application that allows users to create an account, search for books, view book details, and write reviews. Users can also directly search for a book's information using the /api/<isbn> route. 

These are the technologies I used for my project:
- **Languages:** Python, SQL, HTML, CSS
- **Frameworks/Libraries:** Flask, SQLAlchemy, Bootstrap
- **Database:** PostgreSQL
- **API:** Google Books API

Below are some of the challenges I faced while working on the project.
- When users reload the webpage, a 405 Method Not Allowed error response pops up. I have yet to figure out the 
- For this project, I also utilized Flask-Session. I had difficulties storing certain attributes in session. The only item I successfully set in the session was the user's ID number ( 1, 2, 3, ..., n). This unique ID number is the serial primary key of the 'users' table in the database. 

(STILL UPDATING README)