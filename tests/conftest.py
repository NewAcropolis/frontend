import os
import sys
from uuid import uuid4

from bs4 import BeautifulSoup

import pytest
from mock import Mock

from app import create_app

# Don't import ndb to avoid importing google.appengine.ext
sys.modules['app.settings'] = Mock()
sys.modules['app.gaesession'] = Mock()
sys.modules['app.cache'] = Mock()

AUTH_USERNAME = 'user'
AUTH_PASSWORD = 'pass'


@pytest.yield_fixture(scope='session')
def app():
    _app = create_app(**{
        'TESTING': True,
        'PREFERRED_URL_SCHEME': 'http',
        'ADMIN_CLIENT_ID': 'admin',
        'ADMIN_CLIENT_SECRET': 'secret',
        'API_BASE_URL': 'http://na_api_base',
        'SECRET_KEY': 'secret_key',
        'AUTH_USERNAME': AUTH_USERNAME,
        'AUTH_PASSWORD': AUTH_PASSWORD,
        'OAUTHLIB_INSECURE_TRANSPORT': True,
        'WTF_CSRF_ENABLED': False,
    })

    # just return the date to make strfdate available in jinja2
    @_app.template_filter('strfdate')
    def __jinja2_filter_datetime(date, fmt=None):
        return date

    ctx = _app.app_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.fixture
def os_environ():
    """
    clear os.environ, and restore it after the test runs
    """
    # for use whenever you expect code to edit environment variables
    old_env = os.environ.copy()

    class EnvironDict(dict):
        def __setitem__(self, key, value):
            assert type(value) == str
            super(EnvironDict, self).__setitem__(key, value)

    os.environ = EnvironDict()
    yield
    os.environ = old_env


@pytest.fixture
def user_not_authenticated(mocker):
    mocker.patch('app.session', return_value={})


def request(url, method, data=None, headers=None):
    r = method(url, data=data, headers=headers)
    r.soup = BeautifulSoup(r.get_data(as_text=True), 'html.parser')
    return r


@pytest.fixture(scope='function')
def client(app, user_not_authenticated):
    with app.test_request_context(), app.test_client() as client:
        yield client


@pytest.fixture
def logged_in(mocker, user_not_authenticated):
    class Request(object):
        class Authorization(object):
            username = AUTH_USERNAME
            password = AUTH_PASSWORD
        authorization = Authorization
    mocker.patch("app.main.views.request", Request)


@pytest.fixture
def invalid_log_in(mocker):
    class Request(object):
        class Authorization(object):
            username = "invalid"
            password = "wrong"
        authorization = Authorization
    mocker.patch("app.main.views.request", Request)


@pytest.fixture
def sample_future_events(mocker):
    events = [
        {
            "id": str(uuid4()),
            "title": "Test title 1",
            "event_type": "Talk",
            "image_filename": "event.png",
            "event_dates": [{
                "event_datetime": "2018-12-30 19:00",
                "end_time": None
            }],
            "event_state": "approved"
        },
        {
            "id": str(uuid4()),
            "title": "Test title 2",
            "event_type": "Talk",
            "image_filename": "event.png",
            "event_dates": [{
                "event_datetime": "2018-12-31 19:00",
                "end_time": "20:30"
            }],
            "event_state": "approved"
        },
        {
            "id": str(uuid4()),
            "title": "Test title 3",
            "event_type": "Introductory Course",
            "image_filename": "event.png",
            "event_dates": [{
                "event_datetime": "2019-01-01 19:00",
                "end_time": None
            }],
            "event_monthyear": "January 2019",
            "event_state": "approved"
        },
        {
            "id": str(uuid4()),
            "title": "Test title 4",
            "event_type": "Workshop",
            "image_filename": "",
            "event_dates": [{
                "event_datetime": "2019-01-02 19:00",
                "end_time": None
            }],
            "event_state": "approved"
        },
    ]

    mocker.patch(
        "app.clients.api_client.ApiClient.get",
        return_value=events
    )
    return events

@pytest.fixture
def sample_past_events_for_cards():
    events = [
        {
            "title": "Test title 5",
            "event_type": "Talk",
            "image_filename": "event.png",
            "event_dates": [{
                "event_datetime": "2018-12-30 19:00",
                "end_time": None
            }],
            "event_state": "approved"
        },
        {
            "title": "Test title 6",
            "event_type": "Talk",
            "image_filename": "event.png",
            "event_dates": [{
                "event_datetime": "2018-12-31 19:00",
                "end_time": None
            }],
            "event_state": "approved"
        },
        {
            "title": "Test title 7",
            "event_type": "Introductory Course",
            "image_filename": "event.png",
            "event_dates": [{
                "event_datetime": "2019-01-01 19:00",
                "end_time": None
            }],
            "event_monthyear": "January 2019",
            "event_state": "approved"
        },
        {
            "title": "Test title 8",
            "event_type": "Workshop",
            "image_filename": "",
            "event_dates": [{
                "event_datetime": "2019-01-02 19:00",
                "end_time": None
            }],
            "event_state": "approved"
        },
    ]

    return events


@pytest.fixture
def sample_future_event(mocker):
    event = {
        "id": str(uuid4()),
        "title": "Test title 1",
        "description": "Test description",
        "event_type": "Talk",
        "image_filename": "event.png",
        "event_dates": [{
            "event_datetime": "2018-12-30 19:00",
            "end_time": None
        }],
        "event_state": "approved"
    }

    return event


@pytest.fixture
def sample_future_event_for_cards(sample_future_event):
    return [sample_future_event]


@pytest.fixture
def sample_articles_summary(mocker):
    articles = [
        {
            'title': 'Article title 1',
            'short_content':
                'some short content 1, some short content 1, some short content 1, some short content 1',
            'very_short_content': 'some short content 1'
        },
        {
            'title': 'Article title 2',
            'short_content':
                'some short content 2, some short content 2, some short content 2, some short content 2',
            'very_short_content': 'some short content 2'
        },
        {
            'title': 'Article title 3',
            'short_content':
                'some short content 3, some short content 3, some short content 3, some short content 3',
            'very_short_content': 'some short content 3'
        },
        {
            'title': 'Article title 4',
            'short_content':
                'some short content 4, some short content 4, some short content 4, some short content 4',
            'very_short_content': 'some short content 4'
        }
    ]

    mocker.patch(
        "app.clients.api_client.ApiClient.get_articles_summary",
        return_value=articles
    )
    return articles


@pytest.fixture
def sample_marketings(mocker):
    marketings = [
        {
            "id": "Test title 1",
            "description": "Search engine"
        },
    ]

    mocker.patch('app.clients.api_client.ApiClient.get_marketings', return_value=marketings)
    return marketings


@pytest.fixture
def sample_latest_magazine(mocker):
    magazine = {"filename": "latest_magazine.pdf"}

    mocker.patch('app.clients.api_client.ApiClient.get_latest_magazine', return_value=magazine)
    return magazine


@pytest.fixture
def mock_sessions(mocker, session_dict={}):
    mocker.patch('app.session', session_dict)
    mocker.patch('app.clients.session', session_dict)
    mocker.patch('app.main.views.session', session_dict)
    mocker.patch('app.main.views.admin.admin.session', session_dict)
    mocker.patch('app.main.views.admin.emails.session', session_dict)
    mocker.patch('app.main.views.admin.events.session', session_dict)
    mocker.patch('app.main.views.os.environ', session_dict)


@pytest.fixture
def mock_admin_logged_in(mocker):
    session_dict = {
        'user': {
            'id': 'test_id',
            'access_area': 'admin'
        },
        'user_profile': {
            'name': 'test name',
            'email': 'test@example.com'
        },
    }

    mock_sessions(mocker, session_dict)
