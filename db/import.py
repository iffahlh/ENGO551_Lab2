import csv
import os
from sqlalchemy import create_engine,MetaData

if os.getenv("DATABASE_URL") == None:
   print("\n DATABASE URL not defined in env \n")

else:
   print(os.getenv("DATABASE_URL"))

engine = create_engine(os.getenv("DATABASE_URL"))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    with engine.connect() as db:
        for isbn, title, author, year in reader:
            db.execute("INSERT INTO books (isbn, title, author, year) VALUES (%(isbn)s, %(title)s, %(author)s, %(year)s)",
                        {"isbn": isbn, "title": title, "author": author, "year": year })
            print(f"Added book with title {title} to table: books.")

if __name__ == "__main__":
    main()