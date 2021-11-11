from flask import url_for

from bs4 import BeautifulSoup

from tests.conftest import mock_sessions


class WhenGettingUsers:
    def it_shows_all_fields_for_new_user_not_checked(self, client, mocker):
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
            },
            {
                'id': 'test id',
                'email': 'new@example.com',
                'access_area': ''
            }
        ]

        mocker.patch('app.api_client.get_users', return_value=users)

        mock_sessions(mocker, session_dict)
        response = client.get(url_for(
            'main.admin_users'
        ), follow_redirects=True)

        assert response.status_code == 200

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')

        rows = page.select('.row')

        row = BeautifulSoup("<html>{}</html>".format(rows[1]), 'html.parser')

        email = row.select_one('.col-2')
        assert email.text.strip() == users[1]['email']

        user_id = row.select_one('.col-2 input')
        assert user_id.get('value') == users[1]['id']

        areas = row.select('.col input')

        assert len([a for a in areas if a.has_attr('checked')]) == 0

    def it_shows_some_checked_fields(self, client, mocker):
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
            },
            {
                'id': 'test id',
                'email': 'new@example.com',
                'access_area': 'email,event,'
            }
        ]

        mocker.patch('app.api_client.get_users', return_value=users)

        mock_sessions(mocker, session_dict)
        response = client.get(url_for(
            'main.admin_users'
        ), follow_redirects=True)

        assert response.status_code == 200

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')

        rows = page.select('.row')

        row = BeautifulSoup("<html>{}</html>".format(rows[1]), 'html.parser')

        email = row.select_one('.col-2')
        assert email.text.strip() == users[1]['email']

        user_id = row.select_one('.col-2 input')
        assert user_id.get('value') == users[1]['id']

        areas = row.select('.col input')

        checked_areas = [a for a in areas if a.has_attr('checked')]

        assert len(checked_areas) == 2
        assert checked_areas[0].get('name') == 'users-0-event'
        assert checked_areas[1].get('name') == 'users-0-email'

    def it_shows_multiple_users_to_manage(self, client, mocker):
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
            },
            {
                'id': 'test id',
                'email': 'new@example.com',
                'access_area': 'email,event,'
            },
            {
                'id': 'test2 id',
                'email': 'new2@example.com',
                'access_area': 'email,magazine,'
            }
        ]

        mocker.patch('app.api_client.get_users', return_value=users)

        mock_sessions(mocker, session_dict)
        response = client.get(url_for(
            'main.admin_users'
        ), follow_redirects=True)

        assert response.status_code == 200

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')

        rows = page.select('.row')

        row = BeautifulSoup("<html>{}{}</html>".format(rows[1], rows[2]), 'html.parser')

        emails = row.select('.col-2')
        assert emails[0].text.strip() == users[1]['email']
        assert emails[1].text.strip() == users[2]['email']

        user_ids = row.select('.col-2 input')
        assert user_ids[0].get('value') == users[1]['id']
        assert user_ids[1].get('value') == users[2]['id']

    def it_does_not_show_users_if_not_admin(self, client, mocker):
        session_dict = {
            'user': {
                'access_area': 'email,'
            },
            'user_profile': {
                'name': 'test name',
                'email': 'test@example.com'
            }
        }
        users = [
            {
                'access_area': 'admin'
            },
            {
                'id': 'test id',
                'email': 'new@example.com',
                'access_area': 'email,event,'
            },
            {
                'id': 'test2 id',
                'email': 'new2@example.com',
                'access_area': 'email,magazine,'
            }
        ]

        mocker.patch('app.api_client.get_users', return_value=users)

        mock_sessions(mocker, session_dict)
        response = client.get(url_for(
            'main.admin_users'
        ), follow_redirects=True)

        assert response.status_code == 200

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')

        user_col = page.select('.row .col-2')
        assert not user_col


class MockData:
    def __init__(self, data):
        self.data = data

class MockUserField:
    @classmethod
    def set_fields(self, data):
        for k, v in data.items():
            setattr(self, k, None)

    def set_values(self, data):
        for k, v in data.items():
            setattr(self, k, MockData(v.get('data')))

class MockForm:
    def validate_on_submit(self):
        return True

    def __init__(self, users):
        self.users = []
        for user in users:
            mock_user_field = MockUserField()
            mock_user_field.set_fields(user)
            mock_user_field.set_values(user)
            self.users.append(mock_user_field)

    def populate_user_form(self, users):
        pass


session_dict = {
    'user': {
        'access_area': 'email,'
    },
    'user_profile': {
        'name': 'test name',
        'email': 'test@example.com'
    }
}

users = [
    {
        'access_area': 'admin'
    },
    {
        'id': 'test id',
        'email': 'new@example.com',
        'access_area': 'email,event,'
    },
    {
        'id': 'test2 id',
        'email': 'new2@example.com',
        'access_area': 'email,magazine,'
    }
]


class WhenPostingUsers:

    def it_updates_user_access_areas(self, client, mocker):

        form_users = [
            {
                'user_id': {
                    'data': 'test id'
                },
                'email': {
                    'data': 'y'
                },
                'order': {
                    'data': 'y'
                },
                'event': {
                    'data': 'y'
                },
                'admin': {},
                'magazine': {
                    'data': 'y'
                },
                'cache': {},
                'announcement': {},
                'article': {},
            },
            {
                'user_id': {
                    'data': 'test2 id'
                },
                'email': {
                    'data': 'y'
                },
                'order': {},
                'admin': {},
                'event': {},
                'magazine': {
                    'data': 'y'
                },
                'cache': {},
                'announcement': {},
                'article': {},
            }
        ]

        mock_form = MockForm(form_users)

        mocker.patch('app.api_client.get_users', return_value=users)
        mock_api_client = mocker.patch('app.api_client.update_user_access_area')
        mocker.patch('app.main.views.admin.admin.UserListForm', return_value=mock_form)

        mock_sessions(mocker, session_dict)
        client.post(url_for(
            'main.admin_users'
        ))

        mock_api_client.assert_called_once_with(users[1]['id'], 'event,email,order,magazine,')

    def it_does_not_update_if_unchanged(self, client, mocker):
        session_dict = {
            'user': {
                'access_area': 'email,'
            },
            'user_profile': {
                'name': 'test name',
                'email': 'test@example.com'
            }
        }
        users = [
            {
                'access_area': 'admin'
            },
            {
                'id': 'test id',
                'email': 'new@example.com',
                'access_area': 'event,email,'
            },
            {
                'id': 'test2 id',
                'email': 'new2@example.com',
                'access_area': 'email,magazine,'
            }
        ]

        form_users = [
            {
                'user_id': {
                    'data': 'test id'
                },
                'email': {
                    'data': 'y'
                },
                'event': {
                    'data': 'y'
                },
                'admin': {},
                'magazine': {},
                'shop': {},
                'announcement': {},
                'article': {},
            },
            {
                'user_id': {
                    'data': 'test2 id'
                },
                'email': {
                    'data': 'y'
                },
                'admin': {},
                'event': {},
                'magazine': {
                    'data': 'y'
                },
                'shop': {},
                'announcement': {},
                'article': {},
            }
        ]

        mock_form = MockForm(form_users)

        mocker.patch('app.api_client.get_users', return_value=users)
        mock_api_client = mocker.patch('app.api_client.update_user_access_area')
        mocker.patch('app.main.views.admin.admin.UserListForm', return_value=mock_form)

        mock_sessions(mocker, session_dict)
        client.post(url_for(
            'main.admin_users'
        ))

        mock_api_client.assert_not_called()
