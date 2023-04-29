from flask import current_app

from app import api_client
from app.main import main
from app.main.views import render_page


@main.route('/magazines')
def magazines():
    magazines = None
    if not current_app.config["SHOW_RESOURCE_MAINTENANCE"]:
        magazines = api_client.get_magazines()

    return render_page(
        'views/magazines.html',
        magazines=magazines
    )
