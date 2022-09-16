from app import api_client
from app.main import main
from app.main.views import render_page

LOOK_AHEAD = 5


@main.route('/magazines')
@main.route('/magazines/<int:offset>')
def magazines(offset=0):
    magazines = api_client.get_magazines()
    start = offset
    end = offset + LOOK_AHEAD

    return render_page(
        'views/magazines.html',
        magazines=magazines[start:end],
        offset=offset
    )
