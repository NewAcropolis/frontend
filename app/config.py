#!/usr/bin/python
import os
from app.settings import Settings


def is_running_app_engine():
    return 'SERVER_SOFTWARE' in os.environ and \
        ('Google App Engine' in os.environ.get('SERVER_SOFTWARE') or
         'Development' in os.environ.get('SERVER_SOFTWARE'))


def get_setting(name, default=None):
    if is_running_app_engine():
        setting = Settings.get_or_set(name)
        return setting if setting != 'NOT SET' else default
    else:
        print('Running with local env vars:', name)
        return os.environ.get(name, default)


class Config(object):
    DEBUG = False
    API_BASE_URL = get_setting('API_BASE_URL')
    IMAGES_URL = get_setting('IMAGES_URL')
    FRONTEND_BASE_URL = get_setting('FRONTEND_BASE_URL')
    ADMIN_CLIENT_ID = get_setting('ADMIN_CLIENT_ID')
    ADMIN_CLIENT_SECRET = get_setting('ADMIN_CLIENT_SECRET')
    SECRET_KEY = get_setting('SECRET_KEY', 'not_secret')
    AUTH_USERNAME = get_setting('AUTH_USERNAME')
    AUTH_PASSWORD = get_setting('AUTH_PASSWORD')
    GOOGLE_OAUTH2_CLIENT_ID = get_setting('GOOGLE_OAUTH2_CLIENT_ID')
    GOOGLE_OAUTH2_CLIENT_SECRET = get_setting('GOOGLE_OAUTH2_CLIENT_SECRET')
    GOOGLE_OAUTH2_REDIRECT_URI = get_setting('GOOGLE_OAUTH2_REDIRECT_URI')
    OAUTHLIB_INSECURE_TRANSPORT = False
    PAYPAL_ACCOUNT = get_setting('PAYPAL_ACCOUNT')
    ACCESS_AREAS = ['admin', 'event', 'email', 'magazine', 'cache', 'announcement', 'article']
    SUMMARY_LIMIT = 190
    ARTICLE_SUMMARY_LIMIT = 110
    SESSION_EXPIRY = get_setting('SESSION_EXPIRY', 30)
    RECAPTCHA_USE_SSL = False
    RECAPTCHA_PUBLIC_KEY = get_setting('RECAPTCHA_PUBLIC_KEY')
    RECAPTCHA_PRIVATE_KEY = get_setting('RECAPTCHA_PRIVATE_KEY')
    RECAPTCHA_OPTIONS = {'theme': 'black'}
    GA_ID = get_setting('GA_ID')
    GA_TM_ID = get_setting('GA_TM_ID')

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_SSL_STRICT = False


class Development(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    OAUTHLIB_INSECURE_TRANSPORT = True


class Preview(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None
    OAUTHLIB_INSECURE_TRANSPORT = True


class Live(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SESSION_PROTECTION = None


configs = {
    'development': Development,
    # 'test': Test,
    'preview': Preview,
    # 'staging': Staging,
    'live': Live,
    # 'production': Live
}
