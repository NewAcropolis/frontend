# coding: utf-8
import base64
import json
from uuid import UUID
from flask import url_for
from mock import Mock

from bs4 import BeautifulSoup


class MockAPIClient:
    def get_limited_events(self):
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
            {
                "event_dates": [
                    {
                        "event_id": "c1af44b3-1bba-4d6d-996a-162072ebbe53",
                        "speakers": [],
                        "end_time": None,
                        "event_datetime": "2018-01-01 19:00",
                        "id": "e630d711-65f9-41d4-b305-f2e7769a08a8"
                    }
                ],
                "fee": 5,
                "event_type": "workshop",
                "old_id": 1,
                "sub_title": None,
                "title": "test_title",
                "image_filename": None,
                "multi_day_conc_fee": 10,
                "multi_day_fee": 12,
                "venue": None,
                "event_type_id": "1289f71f-5127-4b1f-a615-efa94b930a36",
                "conc_fee": 3,
                "booking_code": None,
                "id": "c1af44b3-1bba-4d6d-996a-162072ebbe53",
                "description": "test description"
            }
        ]

    def get_event_types(self):
        return [
            {
                "repeat": 1,
                "event_type": "short course",
                "old_id": 1,
                "created_at": "Thu, 21 Mar 2019 00:24:55 GMT",
                "id": "80285428-b2a1-4f6e-acfb-7e6f4f04bd0b",
                "event_filename": None,
                "fees": [],
                "duration": 45,
                "repeat_interval": 0,
                "event_desc": "test talk"
            }
        ]

    def get_speakers(self):
        return [
            {
                "parent_id": None,
                "title": "Mr",
                "id": "cbbf7c1d-b12b-4c69-a06c-95b462a21268",
                "name": "Paul White"
            }
        ]

    def get_venues(self):
        return [
            {
                "name": "Head office",
                "old_id": 1,
                "default": True,
                "address": "10 London Street, N1 1NN",
                "directions": "By bus: 100, 111, 123",
                "id": "83f4e670-bb46-4282-a2a0-aead23de6c0d"
            }
        ]


class WhenShowingEvents:
    def it_populates_all_fields_in_admin_events(self, client, mocker, mock_admin_logged_in):
        mocker.patch('app.main.views.admin.events.api_client', MockAPIClient())

        response = client.get(url_for(
            'main.admin_events'
        ))

        assert response.status_code == 200

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')

        select_events = page.select_one('#events')

        event_options = select_events.select('option')

        assert len(event_options) == 3

        assert event_options[0].text == 'New event'
        assert str(event_options[1]) == (
            '<option value="9ad571e1-4b5e-49af-a814-0958b23888c5">2018-01-20'
            ' 19:00 - short course - 2018 event</option>')
        assert str(event_options[2]) == (
            '<option value="c1af44b3-1bba-4d6d-996a-162072ebbe53">2018-01-01 19:00 - workshop - test_title</option>')

        select_event_types = page.select_one('#event_type')

        event_type_options = select_event_types.select('option')

        assert str(event_type_options[0]) == (
            '<option value="80285428-b2a1-4f6e-acfb-7e6f4f04bd0b">short course</option>')

        select_venues = page.select_one('#venue')

        venue_options = select_venues.select('option')

        assert str(venue_options[0]) == (
            '<option value="83f4e670-bb46-4282-a2a0-aead23de6c0d">Head office - 10 London Street, N1 1NN</option>')


class WhenCallingAjaxDeleteEvent:
    def it_makes_delete_api_call(self, client, mocker):
        mock_delete_event = mocker.patch('app.main.views.admin.events.api_client.delete_event')

        response = client.get(url_for('main._delete_event', event_id='9ad571e1-4b5e-49af-a814-0958b23888c5'))

        assert response.status_code == 302
        args = mock_delete_event.call_args_list[0]
        arg, _ = args
        assert arg == (UUID('9ad571e1-4b5e-49af-a814-0958b23888c5'),)


class WhenCallingAjaxGetEvent:
    def it_makes_get_api_call(self, client, mocker):
        mocker.patch(
            'app.main.views.admin.events.session',
            {
                'events': [
                    {'id': 'test', 'description': '&pound;test description'}
                ]
            }
        )

        response = client.get(url_for('main._get_event', event='test'))

        assert response.status_code == 200
        data = json.loads(response.get_data(as_text=True))
        assert data == {'description': u'£test description', 'id': 'test'}


class WhenSubmittingEventsForm:
    def it_uploads_a_file(self, client, mocker, mock_admin_logged_in):
        mock_api_client = MockAPIClient()
        mock_api_client.add_event = Mock()
        mock_api_client.add_event.return_value = {'id': 'test_id'}
        mocker.patch('app.main.views.admin.events.api_client', mock_api_client)

        mock_request = Mock()
        mock_request.files.get.return_value = Mock()
        mock_request.files.get.return_value.read.return_value = 'test data'

        mocker.patch('app.main.views.admin.events.request', mock_request)

        data = {
            'events': '',
            'event_type': '80285428-b2a1-4f6e-acfb-7e6f4f04bd0b',
            'event_dates': '[{"event_date": "2019-03-23 19:00", "end_time": "21:00"}]',
            'description': '<test>',
            'speakers': '',
            'alt_event_images': '',
            'title': 'test title',
            'venue': '83f4e670-bb46-4282-a2a0-aead23de6c0d',
            'reject_reasons_json': '[]',
        }

        response = client.post(
            url_for('main.admin_events'),
            data=data
        )

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        href = page.select_one('a')['href']

        assert mock_api_client.add_event.call_args[0][0]['event_dates'] == json.loads(
            '[{"event_date": "2019-03-23 19:00", "end_time": "21:00"}]')
        assert mock_api_client.add_event.call_args[0][0]['image_data'] == base64.b64encode('test data')
        assert mock_api_client.add_event.call_args[0][0]['description'] == '&lt;test&gt;'
        assert href == '{}/{}'.format(url_for('main.admin_events'), 'test_id')

    def it_uses_an_existing_image_file(self, client, mocker, mock_admin_logged_in):
        mock_api_client = MockAPIClient()
        mock_api_client.add_event = Mock()
        mock_api_client.add_event.return_value = {'id': 'test_id'}
        mocker.patch('app.main.views.admin.events.api_client', mock_api_client)

        mock_request = Mock()
        mock_request.files.get.return_value = None

        mocker.patch('app.main.views.admin.events.request', mock_request)

        data = {
            'events': '',
            'event_type': '80285428-b2a1-4f6e-acfb-7e6f4f04bd0b',
            'event_dates': '[{"event_date": "2019-03-23 19:00", "end_time": "21:00"}]',
            'description': '<test>',
            'speakers': '',
            'alt_event_images': '',
            'title': 'test title',
            'venue': '83f4e670-bb46-4282-a2a0-aead23de6c0d',
            'reject_reasons_json': '[]',
            'image_filename': None,
            'existing_image_filename': 'test.png'
        }

        response = client.post(
            url_for('main.admin_events'),
            data=data
        )

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        href = page.select_one('a')['href']

        assert mock_api_client.add_event.call_args[0][0]['event_dates'] == json.loads(data['event_dates'])
        assert mock_api_client.add_event.call_args[0][0]['image_filename'] == 'test.png'
        assert 'image_data' not in mock_api_client.add_event.call_args[0][0].keys()
        assert mock_api_client.add_event.call_args[0][0]['description'] == '&lt;test&gt;'
        assert href == '{}/{}'.format(url_for('main.admin_events'), 'test_id')

    def it_updates_an_event(self, client, mocker, mock_admin_logged_in):
        mock_api_client = MockAPIClient()
        mock_api_client.update_event = Mock()
        mock_api_client.update_event.return_value = {'id': 'test_id'}
        mocker.patch('app.main.views.admin.events.api_client', mock_api_client)

        mock_request = Mock()
        mock_request.files.get.return_value = None

        mocker.patch('app.main.views.admin.events.request', mock_request)

        data = {
            'events': '9ad571e1-4b5e-49af-a814-0958b23888c5',
            'event_type': '80285428-b2a1-4f6e-acfb-7e6f4f04bd0b',
            'event_dates': '[{"event_date": "2019-03-23 19:00", "end_time": "21:00"}]',
            'description': '<test>',
            'speakers': '',
            'alt_event_images': '',
            'title': 'test title',
            'venue': '83f4e670-bb46-4282-a2a0-aead23de6c0d',
            'reject_reasons_json': '[]',
            'image_filename': None,
            'existing_image_filename': 'test.png'
        }

        response = client.post(
            url_for('main.admin_events'),
            data=data
        )

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        href = page.select_one('a')['href']

        assert mock_api_client.update_event.call_args[0][0] == data['events']
        assert mock_api_client.update_event.call_args[0][1]['event_dates'] == json.loads(data['event_dates'])
        assert mock_api_client.update_event.call_args[0][1]['image_filename'] == 'test.png'
        assert mock_api_client.update_event.call_args[0][1]['description'] == '&lt;test&gt;'
        assert href == '{}/{}/{}'.format(url_for('main.admin_events'), 'test_id', 'event%20updated')
