


CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    firstname VARCHAR NOT NULL,
    lastname  VARCHAR NOT NULL,
    passw     VARCHAR NOT NULL

);


CREATE TABLE books(
   
   isbn VARCHAR PRIMARY KEY,
   title  VARCHAR NOT NULL,
   author VARCHAR NOT NULL,
   year VARCHAR NOT NULL

);

CREATE TABLE reviews (
   
    review VARCHAR NOT NULL,
    book_ibsn VARCHAR REFERENCES books,
    user_id INTEGER  REFERENCES users
    
);

CREATE TABLE ratings (
 
    rating_user_id INTEGER   REFERENCES  users,
    rating INTEGER NOT NULL,
    rating_book_ibsn VARCHAR REFERENCES  books
 
    
);