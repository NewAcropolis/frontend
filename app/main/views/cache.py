from flask import current_app, jsonify
import hashlib

from app.main import main
from app.main.views import requires_auth
from app.main.views.admin.cache import _reload_cache

from app.cache import Cache


@main.route('/cache/reload/<string:key>')
def cache_reload(key):
    if key != hashlib.md5(current_app.config['AUTH_PASSWORD'].encode()).hexdigest():
        return 'Key error', 403
    return _reload_cache()


@main.route('/cache/purge', methods=['GET'])
@requires_auth
def purge_cache():
    return jsonify({"deleted": Cache.purge_cache('get_users')})
