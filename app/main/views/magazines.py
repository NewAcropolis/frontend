from app import api_client
from app.config import use_sim_data
from app.main import main
from app.main.views import render_page


@main.route('/magazines')
@main.route('/magazines/<int:page>')
def magazines(page=0):
    if use_sim_data():
        articles = api_client.get_articles_summary()
        return render_page(
            'views/magazinesV2.html',
            articles=articles
        )
    else:
        magazines = api_client.get_magazines()

        start = page * 5
        end = (page + 1) * 5
        next_page = page + 1

        if end > len(magazines):
            next_page = None

        return render_page(
            'views/magazines.html',
            magazines=magazines[start:end],
            next_page=next_page
        )
