from flask import current_app, render_template, request
import requests
from html import unescape

from app.cache import Cache
from app.main import main
from app.main.views import requires_auth, app_engine_only
from app.queue import Queue
from app.stats import send_ga_event
from app import api_client, csrf


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
        api_base_url=api_client.base_url
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


@main.route('/test/stats/<string:label>')
@main.route('/test/stats/<string:action>/<string:label>')
@main.route('/test/stats/<string:category>/<string:action>/<string:label>')
@main.route('/test/stats/<string:category>/<string:action>/<string:label>/<int:value>')
@requires_auth
def send_test_stats(category='test category', action='test action', label='test label', value=1):
    send_ga_event(category, action, label, value=value)
    return 'sending test stats: {}/{}/{}/{}'.format(category, action, label, value)


@main.route('/ipn/queue', methods=['GET', 'POST'])
@csrf.exempt
def register_ipn():
    data = request.get_data()
    params = request.form.to_dict(flat=False)
    # headers=dict(request.headers)

    params['cmd'] = '_notify-validate'
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
        'user-agent': 'Python-IPN-Verification-Script'
    }
    current_app.logger.info("IPN params: %r", params)  # debug

    r = requests.post(current_app.config['PAYPAL_VERIFY_URL'], params=params, headers=headers, verify=True)
    r.raise_for_status()
    if r.text == 'VERIFIED':
        # add to queue
        current_app.logger.info(f"Verified IPN {params['txn_id']}")
        Queue.add(
            "paypal",
            f"{current_app.config.get('API_BASE_URL')}/orders/paypal/ipn/queued",
            "POST",
            data,
            headers=headers,
            is_json=False
        )
    else:
        current_app.logger.info(f"Unverified IPN {params['txn_id']} - {r.text}")

    return 'ok'


@main.route('/api/check_workers', methods=['GET'])
@app_engine_only
def api_check_workers():
    response = requests.get(current_app.config['API_BASE_URL']).json()
    workers_running = 'workers' in response and response['workers'] == "Running"

    Cache.set_data('api_check_workers', workers_running, is_unique=True)

    if not workers_running:
        return 'no workers', 500

    return 'workers running'


def _unescape_html(items, field_name):
    for item in items:
        item[field_name] = unescape(item[field_name])

    return items
