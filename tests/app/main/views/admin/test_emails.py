from flask import url_for
from mock import Mock

from bs4 import BeautifulSoup


class MockAPIClient:
    def get_future_emails(self):
        return [
            {
                'id': 'test id',
                'subject': 'test subject',
                'event_id': 'test event id',
                'details': '',
                'extra_txt': '',
                'replace_all': False,
                'email_type': 'event',
                'email_state': 'draft',
                'created_at': '2019-07-01 20:00',
                'send_starts_at': '2019-07-14',
                'expires': '2019-07-28'
            }
        ]

    def get_latest_emails(self):
        return [
            {
                'id': 'test id',
                'subject': 'test subject',
                'event_id': 'test event id',
                'details': '',
                'extra_txt': '',
                'replace_all': False,
                'email_type': 'event',
                'email_state': 'draft',
                'created_at': '2019-07-01 20:00',
                'send_starts_at': '2019-07-14',
                'expires': '2019-07-28'
            }
        ]

    def get_email_types(self):
        return [
            {
                'type': 'event'
            },
            {
                'type': 'magazine'
            },
            {
                'type': 'announcement'
            },
        ]

    def get_events_in_future(self):
        return [
            {
                "event_dates": [
                    {
                        "event_id": "9ad571e1-4b5e-49af-a814-0958b23888c5",
                        "speakers": [],
                        "end_time": None,
                        "event_datetime": "2018-01-20 19:00",
                        "id": "fe8e3d17-bef4-48e9-b22b-971cee7276fa"
                    }
                ],
                "fee": 5,
                "event_type": "short course",
                "old_id": 1,
                "sub_title": None,
                "title": "2018 event",
                "image_filename": None,
                "multi_day_conc_fee": 10,
                "multi_day_fee": 12,
                "venue": None,
                "event_type_id": "7818e99a-8c54-40a3-a790-306d9694c4b9",
                "conc_fee": 3,
                "booking_code": None,
                "id": "9ad571e1-4b5e-49af-a814-0958b23888c5",
                "description": "test description"
            },
        ]

    def get_marketings(self):
        return [
            {
                'id': 'test_marketing',
                'description': 'Test'
            }
        ]


class WhenShowingEmails:

    def it_populates_all_fields_in_admin_emails(self, client, mocker, mock_admin_logged_in):
        mocker.patch('app.main.views.admin.emails.api_client', MockAPIClient())

        response = client.get(url_for(
            'main.admin_emails'
        ))

        assert response.status_code == 200

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')

        select_emails = page.select_one('#emails')
        email_options = select_emails.select('option')

        assert len(email_options) == 2

        assert email_options[0].text == 'New email'
        assert str(email_options[1]) == (
            '<option value="test id">test subject</option>')

        select_email_types = page.select_one('#email_types')

        email_type_options = select_email_types.select('option')

        assert str(email_type_options[0]) == '<option value="event">event</option>'
        assert str(email_type_options[1]) == '<option value="magazine">magazine</option>'
        assert str(email_type_options[2]) == '<option value="announcement">announcement</option>'


class WhenSubmittingEmailsForm:

    def it_calls_add_email_if_no_email_id(self, mocker, client, mock_admin_logged_in):
        mock_api_client = MockAPIClient()
        mock_api_client.add_email = Mock()
        mock_api_client.add_email.return_value = {'id': 'test_id'}

        mocker.patch('app.main.views.admin.emails.api_client', mock_api_client)

        data = {
            'emails': '',
            'events': '9ad571e1-4b5e-49af-a814-0958b23888c5',
            'email_types': 'event',
            'email_states': 'draft',
            'send_starts_at': '2019-08-01',
            'expires': '2019-08-14',
        }
        client.post(
            url_for('main.admin_emails'),
            data=data
        )

        assert mock_api_client.add_email.call_args[0][0]['event_id'] == data['events']

    def it_calls_update_email_if_email_id_given(self, mocker, client, mock_admin_logged_in):
        mock_api_client = MockAPIClient()
        mock_api_client.update_email = Mock()
        mock_api_client.update_email.return_value = {'id': 'test_id'}

        mocker.patch('app.main.views.admin.emails.api_client', mock_api_client)

        data = {
            'emails': 'test id',
            'events': '9ad571e1-4b5e-49af-a814-0958b23888c5',
            'email_types': 'event',
            'email_states': 'draft',
            'send_starts_at': '2019-08-01',
            'expires': '2019-08-14',
        }

        client.post(
            url_for('main.admin_emails'),
            data=data
        )

        assert mock_api_client.update_email.call_args[0][0] == data['emails']
        assert mock_api_client.update_email.call_args[0][1]['event_id'] == data['events']
