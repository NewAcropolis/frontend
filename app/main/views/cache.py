from flask import current_app, jsonify
import hashlib

from app.main import main
from app.main.views import requires_auth, app_engine_only
from app.main.views.admin.cache import _reload_cache
from app.cache import Cache
from app.clients.utils import purge_old_tmp_files


@main.route('/cache/reload')
@app_engine_only
def cache_reload(key):
    return _reload_cache()


@main.route('/cache/purge', methods=['GET'])
@requires_auth
def purge_cache():
    return jsonify({"deleted": Cache.purge_cache('get_users')})


@main.route('/tmp_files/purge', methods=['GET'])
@requires_auth
def purge_tmp_files():
    return purge_old_tmp_files()
