import os
import sys


from flask import Flask, session, render_template, request, redirect, url_for, jsonify
import requests
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import copy

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))



@app.route("/")
def home():
    return render_template("index.html")



@app.route("/register", methods=[ "GET", "POST"])
def register():
  
    if  request.method == "GET":
        return "please submit the form instead"
    else:
        username = request.form.get("Username")
        firstname = request.form.get("Firstname")
        lastname = request.form.get("Lastname")
        passw = request.form.get("Password")
        if not len(username) and len(firstname) and len(lastname) and  len(passw) != 0: 
        
            message = "one of the fields is empty, please type all fields to register"
            return render_template("incorrectregister.html", message=message)
        elif db.execute("SELECT  * FROM users WHERE username=:username",{"username":username}).rowcount != 0:
                message="this username has already been used, try something else"
                return render_template("incorrectregister.html", message=message)
        
        else:

           db.execute( "INSERT INTO users (username, firstname, lastname, passw) VALUES(:username, :firstname, :lastname, :passw)", {"username":username,"firstname":firstname, "lastname":lastname, "passw":passw})
           db.commit()
           
           return render_template("register.html", Username=username)

@app.route("/login", methods=[ "GET", "POST"])
def login():
    if  request.method == "GET":
        return "please submit the form instead"
    else:
       Username = request.form.get("Username") 
       passw = request.form.get("Password") 
      # look for the usernames with the referred password
       usernames = db.execute("SELECT  username FROM users WHERE passw=:passw",{"passw":passw}).fetchall()
     
       if len(usernames) == 0:
           return render_template("incorrectlogin.html", Username=Username)
       else:
           #this is to check  whether for given password username also matches
            for name  in usernames:
              
                if name.username  == Username:

                    session["user"]= Username
                    return render_template("login.html", Username=Username)
               
       return render_template("incorrectlogin.html", Username=Username)

@app.route("/logout", methods=[ "GET", "POST"])
def logout(): 
   
    username=session.pop("user")
    return redirect(url_for('home'))


@app.route("/search", methods=[ "GET", "POST"])
def search():
    if  request.method == "GET":
        return "please type the book name"
    else:
       search ="%"+request.form.get("search")+"%"
       
       titles=db.execute("SELECT title FROM books WHERE  isbn LIKE  :search OR title LIKE  :search  OR  author LIKE :search", {"search" : search}).fetchall()
      
       if len(titles) == 0:
           message="The book(s) typed has not been found"
        
           return render_template("login.html", message=message)
       else:
           return render_template("login.html", titles=titles)
      
@app.route("/search/<book_title>", methods=[ "GET", "POST"]) 
def book(book_title):
    thebook=db.execute("SELECT * FROM books WHERE title=:title",{"title":book_title}).fetchone()
   
    if thebook is None:
        return render_template("error.html", message="no such book found")
    else:
      
        session["isbn"]=thebook.isbn   # need this data for writing reviews( in review route)
        username= session.get("user") # to find data about already made reviews and ratings 
        bookreviews=db.execute("SELECT review,  username  FROM reviews  JOIN users  ON users.id=reviews.user_id WHERE book_ibsn=:book_ibsn ",{"book_ibsn":thebook.isbn} ).fetchall()
        bookratings=db.execute(" SELECT  rating , username FROM  ratings JOIN users ON users.id=ratings.rating_user_id WHERE rating_book_ibsn=:rating_book_ibsn ",{"rating_book_ibsn":thebook.isbn} ).fetchall() 
        print(bookreviews)
        print(bookratings)
        listCommon, bookreviews, bookratings = findCommon(bookreviews,bookratings) #needed this to seperate out so that we can distinguish some users who made only reviews or ratings from those who made both
        dataDictionary=readjason(thebook.isbn)
        score=dataDictionary.get('average_rating')
        count=dataDictionary.get('work_ratings_count')
        return render_template("book.html", thebook=thebook, username=username, bookreviews=bookreviews,listCommon=listCommon, bookratings=bookratings, score=score, count=count)
        
@app.route("/review", methods=[ "GET", "POST"])
def review():
  
    review= request.form.get("review") 
    username= session.get("user")
    book_ibsn=session.get("isbn")
    data=db.execute("SELECT  *  FROM users WHERE username=:username ",{"username":username }).fetchone()
    user_id=data.id
  
   
    if  db.execute("SELECT  * FROM reviews WHERE user_id=:user_id AND book_ibsn=:book_ibsn", {"user_id":user_id, "book_ibsn":book_ibsn}).rowcount != 0:
        message="youalready have submitted review for this book"
        return render_template("review.html", message=message)  
    else:
        db.execute("INSERT INTO reviews(review, book_ibsn, user_id) VALUES (:review, :book_ibsn, :user_id)", {"review" :review, "book_ibsn":book_ibsn, "user_id":user_id})
        db.commit()
        message="review submitted"
        return render_template("review.html", message=message)  


@app.route("/rate", methods=[ "GET", "POST"])
def rate():  
    rating= request.form.get("rate") 
    username= session.get("user")
    book_ibsn=session.get("isbn")
    data=db.execute("SELECT  *  FROM users WHERE username=:username ",{"username":username }).fetchone()
    user_id=data.id
  
   
    if  db.execute("SELECT  * FROM ratings WHERE rating_user_id=:rating_user_id AND rating_book_ibsn=:rating_book_ibsn", {"rating_user_id":user_id, "rating_book_ibsn":book_ibsn}).rowcount != 0:
        message="you have already submitted rating for this book"
        return render_template("review.html", message=message)  
    else:
        db.execute("INSERT INTO ratings (rating_user_id, rating, rating_book_ibsn) VALUES (:rating_user_id, :rating, :rating_book_ibsn)", {"rating_user_id":user_id, "rating" :rating, "rating_book_ibsn":book_ibsn})
        db.commit()
        message="rating submitted"
    return    render_template("review.html", message=message)      

@app.route("/backhome")
def backhome():
    return redirect (url_for('home'))

@app.route("/api/<isbn>", methods=[ "GET"])
def api(isbn):
   
    data=db.execute("SELECT * FROM books WHERE  isbn=:isbn",{"isbn": isbn}).fetchone()
    reviewcount=db.execute("SELECT review from reviews WHERE book_ibsn=:book_ibsn", {"book_ibsn":isbn}).rowcount
    allscores=db.execute("SELECT rating from ratings WHERE rating_book_ibsn=:rating_book_ibsn", {"rating_book_ibsn":isbn}).fetchall()
    dataDictionary=readjason(isbn)
    scoreGodreads=dataDictionary.get('average_rating')
    countGodreads=dataDictionary.get('work_ratings_count')
    count=0   
    for each in allscores:
        count+=each.rating
    #averege is calculated by ratings obtained from goodreads and from users registered on this page
    averege=(countGodreads*float(scoreGodreads)+count)/(countGodreads+len(allscores))
   
 
    return jsonify({
                "title":data.title,
                "author":data.author,
                "isbn":data.isbn,
                "review_count": reviewcount,
                "averege_score":averege
    })


def readjason(isbn):
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "Nt515f9m7HmKZQWNqXdOQ" , "isbns": isbn})
    if res.status_code != 200:
        raise Exception("error: API reqsuest not successful")
    else:
        data=res.json()

        dataList= data['books']
        dataDictionary=dataList[0]
        return dataDictionary

def   findCommon(bookreviews,bookratings):
        copybookreviews=copy.deepcopy(bookreviews) #to avoid aliasing
        copybookratings=copy.deepcopy(bookratings)
        listCommon =[]
        if len(bookreviews) and len(bookratings) > 0:
            for data in bookreviews:
                for moredata in bookratings:
                   
                    if data.username == moredata.username:
                      
                       name=data.username
                       rev=data.review
                       rat=moredata.rating
                       mytuple=(name, rev, rat )
                       listCommon.append(mytuple)
                       copybookreviews.remove(data) #delete data from here and not from original list to not mess up numbering order in loop
                       copybookratings.remove(moredata) # same here as above
                    
        return listCommon, copybookreviews, copybookratings