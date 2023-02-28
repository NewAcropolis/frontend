from flask import url_for
from mock import Mock
import pytest

from bs4 import BeautifulSoup
from app.config import Config
from app.clients.errors import HTTPError
from tests.conftest import mock_sessions

def mock_oauth2session(mocker, auth_url, email=None):

    if email:
        _email = email
    else:
        _email = 'test@example.com'

    class MockOAuth2Session:
        def __init__(*args, **kwargs):
            pass

        def authorization_url(self, url):
            return auth_url, 'mock_state'

        def fetch_token(*args, **kwargs):
            return 'mock_token'

        def get(self, url):

            class MockProfile:
                def json(self):
                    return {
                        'name': 'test user',
                        'email': _email
                    }

            return MockProfile()

    mocker.patch('app.main.views.OAuth2Session', MockOAuth2Session)


@pytest.fixture
def access_areas():
    access_areas = [
        '{}{}'.format(
            'Events / Attendance' if a == 'event' else ('Caches / Queue' if a == 'cache' else a.capitalize()),
            's' if a not in ['cache', 'shop', 'event'] else '')
        for a in Config.ACCESS_AREAS if a != 'admin'
    ]
    access_areas.append('Users')
    return access_areas


class WhenAccessingAdminPagesWithoutLoggingIn(object):

    def it_redirects_to_google_auth(self, client, mocker):
        mock_oauth2session(mocker, 'http://auth_url')

        mock_sessions(mocker)

        response = client.get(url_for(
            'main.admin'
        ))
        assert response.status_code == 302
        assert response.location == 'http://auth_url'

    def it_stores_the_profile_in_session(self, client, mocker):
        mock_oauth2session(mocker, url_for('main.callback'))

        session_dict = {
            'oauth_state': 'state'
        }
        mock_sessions(mocker, session_dict)

        mocker.patch('app.main.views.os.environ', {})
        mocker.patch('app.main.views.api_client.get_user', return_value=Mock())

        response = client.get(url_for(
            'main.callback'
        ))
        assert response.status_code == 302
        assert session_dict['user_profile'] == {'name': 'test user', 'email': 'test@example.com'}

    def it_does_not_log_in_email_in_wrong_domain(self, client, mocker):
        mock_oauth2session(mocker, url_for('main.callback'), 'test@invalid_domain.com')

        session_dict = {
            'oauth_state': 'state'
        }
        mock_sessions(mocker, session_dict)

        class MockResponse:
            status_code = 400

            def json(self):
                return {'message': 'test@invalid_domain.com not in correct domain'}

        class MockException:
            response = MockResponse()

        e = HTTPError.create(MockException())

        mocker.patch('app.main.views.os.environ', {})
        mocker.patch('app.main.views.api_client.get_user', return_value=None)
        mocker.patch('app.main.views.api_client.create_user', side_effect=e)

        response = client.get(url_for(
            'main.callback'
        ))

        assert response.status_code == 200
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        err_message = page.select_one('.col-sm')
        assert err_message.text.strip() == 'test@invalid_domain.com not in correct domain, '\
            'please contact the website administrators to get an email in correct domain'


class WhenAccessingAdminPagesAfterLogin(object):

    def it_shows_all_areas_for_admin(self, client, mocker, access_areas):
        session_dict = {
            'user': {
                'access_area': 'admin'
            },
            'user_profile': {
                'name': 'test name',
                'email': 'test@example.com'
            }
        }
        users = [
            {
                'access_area': 'admin'
            }
        ]
        mock_sessions(mocker, session_dict)
        mocker.patch('app.api_client.get_users', return_value=users)
        mocker.patch('app.Cache.get_data', return_value=True)

        response = client.get(url_for(
            'main.admin'
        ), follow_redirects=True)

        assert response.status_code == 200

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')

        areas = page.select('#content .row div')
        assert len(areas) == 8

        area_strs = [a.text.strip() for a in areas]
        assert set(access_areas) == set(area_strs)

    @pytest.mark.parametrize('areas', [
        'email,', 'email,event', 'event,article,magazine'
    ])
    def it_restricts_areas_for_non_admin(self, client, mocker, areas):
        session_dict = {
            'user': {
                'access_area': areas
            },
            'user_profile': {
                'name': 'test name',
                'email': 'test@example.com'
            }
        }
        users = [
            {
                'access_area': areas
            }
        ]
        mock_sessions(mocker, session_dict)
        mocker.patch('app.api_client.get_users', return_value=users)
        mocker.patch('app.Cache.get_data', return_value=True)

        response = client.get(url_for(
            'main.admin'
        ), follow_redirects=True)

        assert response.status_code == 200

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')

        _areas = page.select('#content .row div')
        areas = [
            "{}".format("Events / Attendance" if a == 'event' else a.capitalize() + 's')
            for a in areas.split(',') if a
        ]
        assert len(_areas) == len(areas)

        area_strs = [a.text.strip() for a in _areas]
        assert set(area_strs) == set(areas)
