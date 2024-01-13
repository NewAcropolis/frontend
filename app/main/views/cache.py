from flask import current_app, jsonify
import hashlib

from app.main import main
from app.main.views import requires_auth
from app.main.views.admin.cache import _reload_cache

from app.cache import Cache
from app.clients.utils import purge_old_tmp_files


@main.route('/cache/reload/<string:key>')
def cache_reload(key):
    if key != hashlib.md5(current_app.config['AUTH_PASSWORD'].encode()).hexdigest():
        return 'Key error', 403
    return _reload_cache()


@main.route('/cache/purge', methods=['GET'])
@requires_auth
def purge_cache():
    return jsonify({"deleted": Cache.purge_cache('get_users')})


@main.route('/tmp_files/purge', methods=['GET'])
@requires_auth
def purge_tmp_files():
    return purge_old_tmp_files()
