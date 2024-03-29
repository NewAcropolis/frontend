import io
import os
import re

from datetime import datetime
from decimal import Decimal
from flask import Flask, current_app, make_response, render_template, request, session, url_for
from flask_wtf.csrf import CSRFProtect, CSRFError

import textile

from na_common.delivery import statuses as delivery_statuses

from app.cache import Cache
from app.config import use_sim_data
from app.clients.api_client import ApiClient
from app.clients.paypal_client import PaypalClient


__version__ = '1.11.0'

api_client = ApiClient()
paypal_client = PaypalClient()
csrf = CSRFProtect()


def create_app(**kwargs):
    class NDBMiddleware:
        def __init__(self, app):
            self.app = app
            from google.cloud import ndb

            if os.environ.get('IS_APP_ENGINE') == 'True':
                self.client = ndb.Client()
            else:
                import mock
                from google.auth.credentials import Credentials

                credentials = mock.Mock(spec=Credentials)

                self.client = ndb.Client(project="test", credentials=credentials, namespace='ns1')

        def __call__(self, environ, start_response):
            with self.client.context():
                return self.app(environ, start_response)

    application = Flask(__name__)
    application.wsgi_app = NDBMiddleware(application.wsgi_app)
    from app.config import configs

    if os.environ.get('IS_APP_ENGINE') == 'True':
        import google.cloud.logging

        client = google.cloud.logging.Client()
        client.setup_logging()

        import logging

        application.logger.setLevel(logging.INFO)

    environment_state = get_env()

    application.logger.info("Running with {} settings".format(environment_state))
    csrf.init_app(application)
    application.config.from_object(configs[environment_state])
    setup_config(application, configs[environment_state])

    application.config.update(kwargs)
    if not application.config['TESTING']:
        use_gaesession(application)

    init_app(application)

    api_client.init_app(application)
    paypal_client.init_app(application, "PAYPAL_URL")

    from app.main import main as main_blueprint
    application.register_blueprint(main_blueprint)

    return application


def _get_email():
    profile = session.get('user_profile')
    if profile and isinstance(profile, dict) and 'email' in profile:
        return profile['email']


def _get_users_need_access():
    _users = api_client.get_users()
    if _users:
        users = [u for u in _users if not u['access_area']]
        return users


def _user_has_permissions(area):
    access_areas = session['user']['access_area'].split(',')
    if 'admin' in access_areas:
        return True
    return area in access_areas


def _is_admin_user():
    user = session['user']
    return 'admin' in user.get('access_area') or user.get('access_area') == 'admin'


def _get_course_details(topic):
    with io.open("app/templates/course_details/" + topic + ".txt", "r", encoding="utf-8") as f:
        details = f.read()
    return textile.textile(details)


def _get_course_extra(topic):
    with io.open("app/templates/course_details/" + topic + "_extra.txt", "r", encoding="utf-8") as f:
        extra_text = f.read()

    return [textile.textile(e) for e in extra_text.split('==')]


def _get_summary_course_details(topic):
    buffer_for_header = 100
    with open("app/templates/course_details/" + topic + ".txt", "rb") as f:
        details = f.read(current_app.config['SUMMARY_LIMIT'] + buffer_for_header)

    header_length = len(details.decode('utf-8').split('\n')[1])

    # ignore the first line as its the header
    details = ' '.join(details.decode('utf-8').split('\n')[1:])

    # adjust details for header length
    details = details[header_length:current_app.config['SUMMARY_LIMIT'] + header_length]

    # ignore the last word in case it was split
    details = ' '.join(details.split(' ')[:-1])

    html_tag_pattern = r'<.*?>'
    clean_details = re.sub(html_tag_pattern, '', textile.textile(details))

    return clean_details


def _get_shortened_article_text(article, limit=None):
    if not limit:
        limit = current_app.config['ARTICLE_SUMMARY_LIMIT']
    content = article['very_short_content'][: limit - len(article['title'])]

    # ignore the last word in case it was split
    return ' '.join(content.split(' ')[:-1])


def _get_home_banner_files():
    HOME_BANNER_PATH = os.path.join(current_app.static_folder, "images/home_banner/")

    all_static_filenames = os.listdir(HOME_BANNER_PATH)
    img_filenames = [f for f in all_static_filenames if not f.endswith('.txt')]

    banner_files = []
    for img_f in sorted(img_filenames):
        if os.path.exists(HOME_BANNER_PATH + img_f + ".txt"):
            with io.open(HOME_BANNER_PATH + img_f + ".txt", "rb") as f:
                banner_text = f.read()
            banner_text = textile.textile(banner_text.decode('utf-8'))
            banner_files.append({'filename': img_f, 'text': banner_text})
        else:
            banner_files.append({'filename': img_f, 'text': ''})

    return banner_files


def _get_topic_list_elements(topic):
    topics = {}

    topics["timeless_universal"] = "<a href=\"{}\">Timeless & Universal Philosophy</a>".format(
        url_for('main.course_details', topic='timeless_universal'))
    topics["india"] = "<a href=\"{}\">India</a>".format(url_for('main.course_details', topic='india'))
    topics["tibet"] = "<a href=\"{}\">Tibet</a>".format(url_for('main.course_details', topic='tibet'))
    topics["buddhism"] = "<a href=\"{}\">Buddhism</a>".format(url_for('main.course_details', topic='buddhism'))
    topics["china"] = "<a href=\"{}\">China</a>".format(url_for('main.course_details', topic='china'))
    topics["egypt"] = "<a href=\"{}\">Egypt</a>".format(url_for('main.course_details', topic='egypt'))
    topics["greece"] = "<a href=\"{}\">Greece</a>".format(url_for('main.course_details', topic='greece'))
    topics["rome"] = "<a href=\"{}\">Rome</a>".format(url_for('main.course_details', topic='rome'))
    topics["neoplatonic_school"] = "<a href=\"{}\">The Neoplatonic School</a>".format(
        url_for('main.course_details', topic='neoplatonic_school'))
    topics["philosophy_history"] = "<a href=\"{}\">Philosophy of History</a>".format(
        url_for('main.course_details', topic='philosophy_history'))
    topics["human_being_universe"] = "<a href=\"{}\">The Human Being &amp; The Universe</a>".format(
        url_for('main.course_details', topic='human_being_universe'))
    topics["hermetic_tradition"] = "<a href=\"{}\">The Hermetic Tradition</a>".format(
        url_for('main.course_details', topic='hermetic_tradition'))

    def get_blue_span(text):
        return '<span class="blue_text">{}</span>'.format(text)

    if topic == 'timeless_universal':
        topics["timeless_universal"] = get_blue_span('Timeless & Universal Philosophy')
    elif topic == 'india':
        topics["india"] = get_blue_span('India')
    elif topic == 'tibet':
        topics["tibet"] = get_blue_span('Tibet')
    elif topic == 'buddhism':
        topics["buddhism"] = get_blue_span('Buddhism')
    elif topic == 'china':
        topics["china"] = get_blue_span('China')
    elif topic == 'egypt':
        topics["egypt"] = get_blue_span('Egypt')
    elif topic == 'greece':
        topics["greece"] = get_blue_span('Greece')
    elif topic == 'rome':
        topics["rome"] = get_blue_span('Rome')
    elif topic == 'neoplatonic_school':
        topics["neoplatonic_school"] = get_blue_span('The Neoplatonic School')
    elif topic == 'philosophy_history':
        topics["philosophy_history"] = get_blue_span('Philosophy of History')
    elif topic == 'human_being_universe':
        topics["human_being_universe"] = get_blue_span('The Human Being &amp; The Universe')
    elif topic == 'hermetic_tradition':
        topics["hermetic_tradition"] = get_blue_span('The Hermetic Tradition')

    return topics


def is_not_live():
    return any(host in current_app.config['API_BASE_URL'] for host in [
        'http://localhost', 'https://preview', 'https://test'])


def _get_paypal_url():
    if is_not_live():
        return "https://www.sandbox.paypal.com/cgi-bin/webscr"
    return "https://www.paypal.com/cgi-bin/webscr"


def _get_paypal_base():
    if is_not_live():
        return "https://www.sandbox.paypal.com"
    return "https://www.paypal.com"


def _api_workers_running():
    return Cache.get_data('api_check_workers', default=None)


def _get_images_url():
    if use_sim_data():
        return '/static/images'
    else:
        return current_app.config['IMAGES_URL']


def _get_standard_image_url(image_filename=''):
    if use_sim_data():
        return '/static/images'
    else:
        if image_filename:
            if '/tmp/' in image_filename:
                return f"{current_app.config['IMAGES_URL']}{image_filename}"
            else:
                return f"{current_app.config['IMAGES_URL']}/standard/{image_filename}"
        else:
            return current_app.config['IMAGES_URL']


def _strfdate(date):
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    return date_obj.strftime('%A %-d %B')


def _to_decimal(num):
    return Decimal(num)

def _format_price(price):
    price = Decimal(price)
    _price = str('{:.2f}'.format(price))

    return f"£{_price}"


def init_app(app):
    app.jinja_env.globals['API_BASE_URL'] = app.config['API_BASE_URL']
    app.jinja_env.globals['get_images_url'] = _get_images_url
    app.jinja_env.globals['get_standard_image_url'] = _get_standard_image_url
    app.jinja_env.globals['get_paypal_url'] = _get_paypal_url
    app.jinja_env.globals['get_paypal_base'] = _get_paypal_base
    app.jinja_env.globals['get_email'] = _get_email
    app.jinja_env.globals['get_users_need_access'] = _get_users_need_access
    app.jinja_env.globals['is_admin_user'] = _is_admin_user
    app.jinja_env.globals['user_has_permissions'] = _user_has_permissions
    app.jinja_env.globals['get_course_details'] = _get_course_details
    app.jinja_env.globals['get_summary_course_details'] = _get_summary_course_details
    app.jinja_env.globals['get_shortened_article_text'] = _get_shortened_article_text
    app.jinja_env.globals['get_course_extra'] = _get_course_extra
    app.jinja_env.globals['get_home_banner_files'] = _get_home_banner_files
    app.jinja_env.globals['get_topic_list_elements'] = _get_topic_list_elements
    app.jinja_env.globals['api_workers_running'] = _api_workers_running
    app.jinja_env.globals['is_not_live'] = is_not_live
    app.jinja_env.globals['get_env'] = get_env
    app.jinja_env.globals['strfdate'] = _strfdate
    app.jinja_env.globals['to_decimal'] = _to_decimal
    app.jinja_env.globals['format_price'] = _format_price
    app.jinja_env.globals['config'] = app.config
    app.jinja_env.globals['delivery_statuses'] = delivery_statuses

    @app.before_request
    def before_request():
        if '/admin' in request.url and not session.get('user'):
            if current_app.config['NO_ADMIN_AUTH']:
                _users = api_client.get_users()
                user = _users[0] if _users \
                    else {'id': '7b0ceea5-a10d-4256-bf84-1830a5093b43', 'name': 'Test User', 'email': 'test@localhost'}

                session['user_profile'] = {
                    'name': user['name'],
                    'email': user['email'],
                }
                session['user'] = {
                    'id': user['id'],  # just use the first user as admin
                    'access_area': 'admin',
                }
            else:
                from app.main.views import google_login
                return google_login()

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
        return response

    @app.errorhandler(Exception)
    def exception(e):
        msg = e.message if hasattr(e, 'message') else "Server error"
        app.logger.exception(e)
        return render_template('errors/errors.html', message=[msg]), e.code if hasattr(e, 'code') else 500

    @app.errorhandler(404)
    def page_not_found(e):
        msg = e.description or "Not found"
        app.logger.exception(msg)
        return render_template('errors/errors.html', message=[msg]), 404

    @app.errorhandler(CSRFError)
    def handle_csrf(err):
        app.logger.warning('csrf.error_message: {}'.format(err))
        app.logger.warning(
            'csrf.invalid_token: Aborting request, user_id: {}'.format(
                session['user']['id'] if 'user' in session else None
            )
        )

        resp = make_response(render_template(
            "errors/errors.html",
            message=['Something went wrong, please go back and try again.']
        ), 400)
        return useful_headers_after_request(resp)


def setup_config(application, config_class):
    application.config.from_object(config_class)


def get_env():
    if request and 'test' in request.args:
        return 'test'
    else:
        return os.environ.get('ENVIRONMENT', 'development')


def get_root_path(application):
    return application.root_path


def use_gaesession(application):
    from app import gaesession
    application.session_interface = gaesession.GaeNdbSessionInterface(application)


def useful_headers_after_request(response):
    response.headers.add('X-Frame-Options', 'deny')
    response.headers.add('X-Content-Type-Options', 'nosniff')
    response.headers.add('X-XSS-Protection', '1; mode=block')
    response.headers.add('Content-Security-Policy', (
        "default-src 'self' {} 'unsafe-inline';"
        "script-src 'self' {} *.google-analytics.com 'unsafe-inline' 'unsafe-eval' data:;"
        "connect-src 'self' *.google-analytics.com;"
        "object-src 'self';"
        "font-src 'self' {} data:;"
    ))
    if 'Cache-Control' in response.headers:
        del response.headers['Cache-Control']
    response.headers.add(
        'Cache-Control', 'no-store, no-cache, private, must-revalidate')
    return response
