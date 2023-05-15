from flask import current_app

from app import api_client
from app.main import main
from app.main.views import render_page


@main.route('/magazinesV2')
def magazinesV2():
    magazines = None
    if not current_app.config["SHOW_RESOURCE_MAINTENANCE"]:
        magazines = api_client.get_magazines()

    return render_page(
        'views/magazinesV2.html',
        magazines=magazines
    )
