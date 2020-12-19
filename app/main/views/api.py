from flask import current_app, render_template
from six.moves.html_parser import HTMLParser

from app.main import main
from app.main.views import requires_auth
from app.stats import send_ga_event
from app import api_client


@main.route('/api')
def api_test():
    return render_template(
        'views/api_test/api.html'
    )


@main.route('/api/speakers')
@requires_auth
def api_speakers():
    speakers = api_client.get_speakers()
    return render_template(
        'views/api_test/speakers.html',
        speakers=speakers
    )


@main.route('/api/venues')
@requires_auth
def api_venues():
    venues = api_client.get_venues()
    return render_template(
        'views/api_test/venues.html',
        venues=venues
    )


@main.route('/api/past_events')
@requires_auth
def api_past_events():
    events = api_client.get_events_past_year()
    return render_template(
        'views/api_test/events.html',
        images_url=current_app.config['IMAGES_URL'],
        events=events,
        api_base_url=api_client.base_url
    )


@main.route('/api/future_events')
@requires_auth
def api_future_events():
    events = api_client.get_events_in_future(approved_only=True)

    return render_template(
        'views/api_test/events.html',
        images_url=current_app.config['IMAGES_URL'],
        events=_unescape_html(events, 'description'),
        api_base_url=api_client.base_url,
        paypal_account=current_app.config['PAYPAL_ACCOUNT']
    )


@main.route('/api/articles/summary')
@requires_auth
def api_articles_summary():
    articles = api_client.get_articles_summary()
    return render_template(
        'views/api_test/articles_summary.html',
        articles=articles
    )


@main.route('/api/article/<uuid:id>')
@requires_auth
def api_article(id):
    article = api_client.get_article(id)
    return render_template(
        'views/api_test/article.html',
        article=article
    )


@main.route('/test/stats/<string:method>/<string:label>')
@main.route('/test/stats/<string:method>/<string:action>/<string:label>')
@main.route('/test/stats/<string:method>/<string:category>/<string:action>/<string:label>')
@requires_auth
def send_test_stats(method='post', category='test category', action='test action', label='test label'):
    send_ga_event(category, action, label, method=method)
    return 'sending test stats {}: {}/{}/{}'.format(method, category, action, label)


def _unescape_html(items, field_name):
    h = HTMLParser()
    for item in items:
        item[field_name] = h.unescape(item[field_name])

    return items
