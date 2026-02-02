import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text

# Change database engine accordingly
engine = create_engine('postgresql://localhost/sherryzhang')

db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute(text("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)"),
                    {"isbn": isbn, "title": title, "author": author, "year": year})
    db.commit()
        
if __name__ == "__main__":
    main()