from bs4 import BeautifulSoup

from flask import url_for
from flask_wtf.csrf import CSRFError


class WhenAccessingPageWithError:
    def it_returns_400_for_csrf_error(self, mocker, client, mock_admin_logged_in):
        csrf_err = CSRFError('400 Bad Request: The CSRF tokens do not match.')
        mocker.patch('app.main.views.admin.admin.render_template', side_effect=csrf_err)

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

        response = client.get(url_for('main.admin_users'))

        assert response.status_code == 400
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        message = page.select_one('.m-1')

        assert message.text.strip() == 'Something went wrong, please go back and try again.'
