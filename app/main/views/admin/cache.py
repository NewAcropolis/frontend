from flask import current_app, jsonify, render_template, session

from app import api_client
from app.main.views.api import api_check_workers
from app.clients.api_client import only_show_approved_events, update_cache
from app.cache import Cache
from app.main import main
from app.selected_tags import SelectedTags


@main.route('/admin/cache')
def cache():
    cache = Cache.get_cache_overview()
    return render_template('views/admin/cache.html', cache=cache)


@main.route('/admin/cache/show/<string:name>')
def cache_show(name):
    cache = Cache.get_cache(name)
    extra = f' ({SelectedTags.get_selected_tags().tags})' if name == 'get_articles_summary_by_tags'\
        and SelectedTags.get_selected_tags() else ''
    return render_template('views/admin/cache_show.html', cache=cache, extra=extra)


@main.route('/admin/_reload_cache')
def _reload_cache():
    if "user_profile" in session:
        current_app.logger.info("Reloading cache: {}".format(session["user_profile"]["name"]))
    else:
        current_app.logger.info("Reloading cache")

    update_cache(
        func=api_client.get_events_in_future_from_db,
        decorator=only_show_approved_events, approved_only=True)
    update_cache(func=api_client.get_limited_events_from_db)
    update_cache(func=api_client.get_users_from_db)
    update_cache(func=api_client.get_events_past_year_from_db)
    update_cache(func=api_client.get_articles_summary_from_db)
    update_cache(func=api_client.get_books_from_db)
    update_cache(func=api_client.get_magazines_from_db)
    update_cache(func=api_client.get_latest_emails_from_db)
    update_cache(func=api_client.get_events_in_future_from_db)
    update_cache(func=api_client.get_venues_from_db)
    update_cache(func=api_client.get_event_types_from_db)
    update_cache(func=api_check_workers)

    Cache.purge_older_versions()

    return jsonify(
        {
            'response':
            'get_events_in_future, get_limited_events, get_events_past_year, get_users, get_events_in_future, '
            'get_articles_summary, get_books, get_magazines, get_latest_emails, api_check_workers, '
            'get_venues, get_event_types, reloaded'
        }
    )


@main.route('/admin/_update_cache/<string:names>')
def _update_cache(names):
    resp = []
    for name in names.split(','):
        if name == 'get_events_in_future':
            updated = update_cache(
                func=api_client.get_events_in_future_from_db,
                decorator=only_show_approved_events, approved_only=True)
        else:
            updated = update_cache(func=getattr(api_client, f"{name}_from_db"))
        resp.append("{}{}".format(name, " updated" if updated else " unchanged"))

    return jsonify(
        {'response': ", ".join(resp)}
    )


@main.route('/admin/_purge_cache')
@main.route('/admin/_purge_cache/<string:name>')
def _purge_cache(name=None):
    current_app.logger.info("Purging {} cache: {}".format(name if name else "all", session["user_profile"]["name"]))

    Cache.purge_cache(name)
    return jsonify({'response': 'cache purged'})


@main.route('/admin/_update_future_events')
def _update_future_events():
    update_cache(func=api_client.get_events_in_future)

    return 'Updating future events'
