from app import api_client
from app.main import main
from app.main.views import render_page


@main.route('/magazines')
@main.route('/magazines/<int:offset>')
def magazines(offset=0):
    magazines = api_client.get_magazines()

    return render_page(
        'views/magazines.html',
        magazines=magazines[start:end],
        offset=offset
    )
