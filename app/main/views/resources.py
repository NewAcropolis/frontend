from app import api_client
from app.main import main
from app.main.views import render_page


@main.route('/resources')
def resources():
    books = api_client.get_books()

    return render_page(
        'views/resources.html',
        books=books
    )
