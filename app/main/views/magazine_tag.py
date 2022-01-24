from flask import current_app, jsonify, request
from functools import wraps
import os

from app.main import main
from app.main.views import requires_auth, app_engine_only
from app.magazine_tag import MagazineTag


@main.route('/magazine_tag', methods=['GET'])
@requires_auth
def show_magazine_tag():
    tags = MagazineTag.get_tags()
    return jsonify(tags)


@main.route('/magazine_tag/reindex', methods=['GET'])
@app_engine_only
def reindex_magazine_tag():
    resp = MagazineTag.reindex()
    return jsonify(resp)