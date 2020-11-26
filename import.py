import os
import csv


from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker



engine = create_engine('postgres://rxtdnbsovwnawy:e30ece14ec689238f33ba9f69284a7b19888dbf52e2de3fe16d415d291abbb99@ec2-54-228-209-117.eu-west-1.compute.amazonaws.com:5432/dfcjbvd62sk7d2')
db = scoped_session(sessionmaker(bind=engine))
def main():
    f= open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        print(title)
        db.execute("INSERT INTO books(isbn, title, author, year) VALUES(:isbn, :title, :author, :year)" ,{"isbn":isbn, "title":title, "author":author, "year": year} )
    db.commit()

    print("works")    

if __name__ == "__main__":
    main()