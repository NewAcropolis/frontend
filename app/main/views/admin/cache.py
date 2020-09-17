from flask import current_app, jsonify, render_template, session

from app import api_client
from app.clients.api_client import (
    get_events_intro_courses_prioritised, only_show_approved_events, update_cache_via_thread)
from app.cache import Cache
from app.main import main


@main.route('/admin/cache')
def cache():
    cache = Cache.get_cache_overview()
    return render_template('views/admin/cache.html', cache=cache)


@main.route('/admin/_reload_cache')
def _reload_cache():
    current_app.logger.info("Resetting cache: {}".format(session["user_profile"]["name"]))

    update_cache_via_thread(
        api_client.get_events_in_future_from_db,
        decorator=only_show_approved_events, approved_only=True)
    update_cache_via_thread(api_client.get_events_past_year_from_db)
    update_cache_via_thread(api_client.get_articles_summary_from_db)

    return jsonify({'response': 'get_events_in_future, get_events_past_year, get_articles_summary reloaded'})


@main.route('/admin/_purge_cache')
def _purge_cache():
    current_app.logger.info("Purging all cache: {}".format(session["user_profile"]["name"]))

    Cache.purge_cache()
    return jsonify({'response': 'cache purged'})


@main.route('/admin/_update_future_events')
def _update_future_events():
    update_cache_via_thread(api_client.get_events_in_future)

    return 'Updating future events'
