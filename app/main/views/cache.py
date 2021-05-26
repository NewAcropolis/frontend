from app.main import main
from app.main.views import requires_auth
from app.main.views.admin.cache import _reload_cache


@main.route('/cache/reload')
@requires_auth
def cache_reload():
    return _reload_cache()
