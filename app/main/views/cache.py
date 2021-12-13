from flask import current_app
import hashlib

from app.main import main
from app.main.views.admin.cache import _reload_cache


@main.route('/cache/reload/<string:key>')
def cache_reload(key):
    if key != hashlib.md5(current_app.config['AUTH_PASSWORD'].encode()).hexdigest():
        return 'Key error', 403
    return _reload_cache()
