from flask import current_app, jsonify, session
from app import api_client
from app.main import main
from app.main.views import render_page


@main.route('/magazines')
def magazines():
    return render_page('views/magazines.html')
