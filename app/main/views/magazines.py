from app import api_client
from app.main import main
from app.main.views import render_page


@main.route('/magazines')
@main.route('/magazines/<int:page>')
def magazines(page=0):
    magazines = api_client.get_magazines()

    start = page * 5
    end = (page + 1) * 5

    return render_page(
        'views/magazines.html',
        magazines=magazines[start:end],
        page=page
    )
