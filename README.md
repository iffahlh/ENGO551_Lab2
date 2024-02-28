# ENGO551_Lab2
This is an extension of [ENGO 551 Lab 1](https://github.com/iffahlh/ENGO551_Lab1), a website that allows registered users to search for book reviews submitted by other registered users, using a database containing up to 5000 books. The following features have been added:
- Ratings using the [Google Books API](https://www.googleapis.com/books/v1/volumes) are now displayed
- Logged in users can now submit their own review, however they are limited to one review per book
- The website returns a json response when users request api/<isbn> method

Demo for the website can be found [here](https://youtu.be/6O_3YQks6ws). Flask, HTML, Bootstrap, and PostgreSQL were used to build this website.

## Files

**db/import.py** - loads books.csv into table books in the PostgreSQL database

**templates/layout.html** - Flask template providing general layout of the website. used as parent of all pages

**templates/404.html** - Flask template for 404 errors

**templates/login.html** - Flask template for login/logout page

**templates/register.html** - Flask template for registering account page

**templates/register_success.html** - Flask template for a page that appears after a user has registered an account successfully 

**templates/search.html** - Flask template for main book search page and search results

**templates/result.html** - Flask template for book information page

**application.py** - Flask application that launches the development server for the website




