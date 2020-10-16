# coding: utf-8
from app.main import main
from app import api_client
from app.main.views import render_page


@main.route('/books')
def books():
    books = api_client.get_books()

    return render_page(
        'views/books.html',
        books=books
    )


@main.route('/book/<uuid:book_id>')
def book_details(book_id):
    book = api_client.get_book(book_id)
    return render_page(
        'views/book.html',
        book=book
    )
