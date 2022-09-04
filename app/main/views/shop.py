from flask import current_app

from app import api_client
from app.main import main
from app.main.views import render_page


@main.route('/shop')
def shop():
    books = None
    if not current_app.config["SHOW_RESOURCE_MAINTENANCE"]:
        books = api_client.get_books()

    return render_page(
        'views/shop.html',
        books=books
    )
