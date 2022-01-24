from flask import jsonify

from app.main import main
from app.main.views import requires_auth, app_engine_only
from app.tag import Tag


@main.route('/tag', methods=['GET'])
@requires_auth
def show_tags():
    tags = Tag.get_tags()
    return jsonify(tags)


@main.route('/tag/reindex/<string:item_type>', methods=['GET'])
@main.route('/tag/reindex', methods=['GET'])
@app_engine_only
def reindex_tag(item_type='magazine'):
    resp = Tag.reindex(item_type)
    return jsonify(resp)
