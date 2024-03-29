#!/usr/bin/python
import os
from flask import request


class Config(object):
    DEBUG = False
    API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost')
    FRONTEND_BASE_URL = os.environ.get('FRONTEND_BASE_URL')
    DOWNLOADS_URL = "/download"
    IMAGES_URL = os.environ.get('IMAGES_URL')
    ADMIN_CLIENT_ID = os.environ.get('ADMIN_CLIENT_ID')
    ADMIN_CLIENT_SECRET = os.environ.get('ADMIN_CLIENT_SECRET')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'not_secret')
    AUTH_USERNAME = os.environ.get('AUTH_USERNAME')
    AUTH_PASSWORD = os.environ.get('AUTH_PASSWORD')
    NO_ADMIN_AUTH = False
    GOOGLE_OAUTH2_CLIENT_ID = os.environ.get('GOOGLE_OAUTH2_CLIENT_ID')
    GOOGLE_OAUTH2_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH2_CLIENT_SECRET')
    GOOGLE_OAUTH2_REDIRECT_URI = os.environ.get('GOOGLE_OAUTH2_REDIRECT_URI')
    OAUTHLIB_INSECURE_TRANSPORT = "False"
    PAYPAL_URL = "https://www.sandbox.paypal.com/"
    PAYPAL_ACCOUNT = os.environ.get('PAYPAL_ACCOUNT')
    PAYPAL_ACCOUNT_ID = os.environ.get('PAYPAL_ACCOUNT_ID')
    PAYPAL_ENCRYPTED = os.environ.get('PAYPAL_ENCRYPTED_1', '') + os.environ.get('PAYPAL_ENCRYPTED_2', '')
    PAYPAL_DELIVERY = os.environ.get('PAYPAL_DELIVERY')
    ACCESS_AREAS = ['admin', 'event', 'email', 'order', 'magazine', 'cache', 'article', 'member']
    SUMMARY_LIMIT = 190
    ARTICLE_SUMMARY_LIMIT = 110
    SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME', 'na-frontend')
    SESSION_EXPIRY = os.environ.get('SESSION_EXPIRY', 30)
    RECAPTCHA_USE_SSL = False
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY')
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY')
    RECAPTCHA_OPTIONS = {'theme': 'black'}
    STORAGE = os.environ.get('GOOGLE_STORE')
    GA_ID = os.environ.get('GA_ID')
    GA_TM_ID = os.environ.get('GA_TM_ID')
    MAX_IMAGE_SIZE = 2 * 1024 * 1024
    QUEUE_EXPIRY = 60 * 24 * 14
    QUEUE_OK_EXPIRY = 60 * 24 * 7
    QUEUE_RETRY_LIMIT = 10
    ENABLE_STATS = os.environ.get('ENABLE_STATS', '') == 'True'
    TESTING = False
    NO_API = False
    DELIVERY_UK = 3.50

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_SSL_STRICT = False

    SHOW_RESOURCE_MAINTENANCE = os.environ.get('SHOW_RESOURCE_MAINTENANCE', '') == 'True'

    TEST_INTRO_IMAGE = os.environ.get('TEST_INTRO_IMAGE')
    TEST_INTRO_BOOKING = os.environ.get('TEST_INTRO_BOOKING')


class Development(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    OAUTHLIB_INSECURE_TRANSPORT = "True"
    NO_ADMIN_AUTH = True
    FACEBOOK_VERIFICATION = "w6adh6kjwrw5c3tmwo6e87o0ij0kgt"
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    STORAGE = os.environ.get('GOOGLE_STORE')
    PAYPAL_VERIFY_URL = "http://localhost:5005"
    NO_API = False


class Live(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    NO_ADMIN_AUTH = False
    FACEBOOK_VERIFICATION = "w6adh6kjwrw5c3tmwo6e87o0ij0kgt"
    PAYPAL_URL = "https://www.paypal.com/"
    PAYPAL_VERIFY_URL = "https://ipnpb.paypal.com/cgi-bin/webscr"
    NO_API = False


class Preview(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    NO_ADMIN_AUTH = False
    FACEBOOK_VERIFICATION = "w6adh6kjwrw5c3tmwo6e87o0ij0kgt"
    PAYPAL_VERIFY_URL = 'https://ipnpb.sandbox.paypal.com/cgi-bin/webscr'


class Review(Config):
    TESTING = True
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    NO_ADMIN_AUTH = True
    IMAGES_URL = "/static/images/review"
    DOWNLOADS_URL = "/static/download"


configs = {
    'development': Development,
    'preview': Preview,
    'review': Review,
    'live': Live,
}


def use_sim_data():
    return os.environ.get('ENVIRONMENT', 'development') == 'review' or (
        os.environ.get('ENVIRONMENT', 'development') != 'live' and request.args.get('test') == 'sim_data'
    )
