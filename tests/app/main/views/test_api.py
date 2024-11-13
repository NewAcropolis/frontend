from datetime import datetime, timedelta
import uuid
from bs4 import BeautifulSoup
from flask import url_for


class WhenAccessingPagesWithoutLoggingIn(object):

    def it_returns_401(self, client, mocker):
        response = client.get(url_for(
            'main.api_speakers'
        ))
        assert response.status_code == 401
        text = response.get_data(as_text=True)
        assert text == "Could not verify your access level for that URL.\nYou have to login with proper credentials"


class WhenAccessingPagesWithIncorrectLogIn(object):

    def it_returns_401(self, client, mocker, invalid_log_in):
        response = client.get(url_for(
            'main.api_speakers'
        ))
        assert response.status_code == 401
        text = response.get_data(as_text=True)
        assert text == "Could not verify your access level for that URL.\nYou have to login with proper credentials"


class WhenAccessingSpeakersPage(object):

    def it_shows_list_of_speakers(self, client, mocker, logged_in):
        mocker.patch(
            "app.clients.api_client.ApiClient.get_speakers",
            return_value=[
                {
                    "title": "Mr",
                    "name": "Test",
                    "alternate_names": "Dr Test"
                }
            ]
        )

        response = client.get(url_for(
            'main.api_speakers'
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        assert page.select_one("#content li").text == 'Mr Test  (Dr Test)'


class WhenAccessingVenuesPage(object):

    def it_shows_list_of_venues(self, client, mocker, logged_in):
        mocker.patch(
            "app.clients.api_client.ApiClient.get_venues",
            return_value=[
                {
                    "name": "London",
                    "address": "19 Test Terrace, N1",
                    "directions": "<div>Bus: 1, 5, 10 2 minutes walk</div>"
                }
            ]
        )

        response = client.get(url_for(
            'main.api_venues'
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        assert page.select_one("#content li").text == 'London: 19 Test Terrace, N1 Bus: 1, 5, 10 2 minutes walk'


class WhenAccessingEventsPastYearPage(object):

    def it_shows_list_of_events_past_year(self, client, mocker, logged_in):
        mocker.patch(
            "app.clients.api_client.ApiClient.get_events_past_year",
            return_value=[
                {
                    "booking_code": "111222XXXYYY",
                    "conc_fee": 3,
                    "description": "Test event description 1",
                    "event_dates": [
                        {
                            "event_datetime": "2018-08-17 19:00",
                            "speakers": []
                        }
                    ],
                    "fee": 5,
                    "image_filename": "2018/test_image.jpg",
                    "multi_day_conc_fee": 0,
                    "multi_day_fee": 0,
                    "old_id": 286,
                    "sub_title": "",
                    "title": "Test title 1",
                    "venue": {
                        "address": "18 Compton Terrace N1 2UN, next door to Union Chapel.",
                        "default": True,
                        "directions": "<div>Bus: Bus routes 4, 19, 30, 43 & 277 stop nearby</div>",
                        "name": "Head Branch",
                    }
                },
                {
                    "booking_code": "222333444XXXZZZ",
                    "conc_fee": 12,
                    "description": "Test description event 2",
                    "event_dates": [
                        {
                            "event_datetime": "2018-09-19 19:00",
                            "speakers": [
                                {
                                    "name": "Various",
                                    "title": None
                                }
                            ]
                        },
                        {
                            "event_datetime": "2018-09-26 19:00",
                            "speakers": [
                                {
                                    "name": "Various",
                                    "title": None
                                }
                            ]
                        },
                        {
                            "event_datetime": "2018-10-03 19:00",
                            "speakers": [
                                {
                                    "name": "Various",
                                    "title": None
                                }
                            ]
                        }
                    ],
                    "fee": 15,
                    "image_filename": "2018/IMG_2122.JPG",
                    "multi_day_conc_fee": 30,
                    "multi_day_fee": 40,
                    "old_id": 288,
                    "sub_title": "",
                    "title": "The Language of Symbols",
                    "venue": {
                        "address": "18 Compton Terrace N1 2UN, next door to Union Chapel.",
                        "default": True,
                        "directions": "<div>Bus: Bus routes 4, 19, 30, 43 & 277 stop nearby</div>",
                        "name": "Head Branch",
                    }
                }
            ]
        )

        response = client.get(url_for(
            'main.api_past_events'
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        assert 'Test event description 1' in page.find('p').text
        assert 'Test description event 2' in page.find('p').text


class WhenAccessingFutureEventsPage(object):
    def it_shows_list_of_approved_events(self, client, mocker, logged_in):
        future_dates = [
            datetime.strftime(datetime.now() + timedelta(days=n + 1), "%Y-%m-%d 19:00") for n in range(4)
        ]

        mocker.patch(
            "app.clients.api_client.ApiClient.get",
            return_value=[
                {
                    "booking_code": "111222XXXYYY",
                    "conc_fee": 3,
                    "description": "Test description draft event",
                    "event_type": 'talk',
                    "event_state": 'draft',
                    "event_dates": [
                        {
                            "event_datetime": future_dates[0],
                            "end_time": None,
                            "speakers": []
                        }
                    ],
                    "fee": 5,
                    "headline": False,
                    "image_filename": "2019/test_image.jpg",
                    "multi_day_conc_fee": 0,
                    "multi_day_fee": 0,
                    "old_id": 286,
                    "sub_title": "",
                    "title": "Test title 1",
                    "venue": {
                        "address": "18 Compton Terrace N1 2UN, next door to Union Chapel.",
                        "default": True,
                        "directions": "<div>Bus: Bus routes 4, 19, 30, 43 & 277 stop nearby</div>",
                        "name": "Head Branch",
                    }
                },
                {
                    "booking_code": "222333444XXXZZZ",
                    "conc_fee": 12,
                    "description": "Test description approved event",
                    "event_type": 'short course',
                    "event_state": 'approved',
                    "event_dates": [
                        {
                            "event_datetime": future_dates[1],
                            "end_time": None,
                            "speakers": [
                                {
                                    "name": "Various",
                                    "title": None
                                }
                            ]
                        },
                        {
                            "event_datetime": future_dates[2],
                            "end_time": None,
                            "speakers": [
                                {
                                    "name": "Various",
                                    "title": None
                                }
                            ]
                        },
                        {
                            "event_datetime": future_dates[3],
                            "end_time": None,
                            "speakers": [
                                {
                                    "name": "Various",
                                    "title": None
                                }
                            ]
                        }
                    ],
                    "fee": 15,
                    "headline": False,
                    "image_filename": "2019/IMG_2122.JPG",
                    "multi_day_conc_fee": 30,
                    "multi_day_fee": 40,
                    "old_id": 288,
                    "sub_title": "",
                    "title": "The Language of Symbols",
                    "venue": {
                        "address": "18 Compton Terrace N1 2UN, next door to Union Chapel.",
                        "default": True,
                        "directions": "<div>Bus: Bus routes 4, 19, 30, 43 & 277 stop nearby</div>",
                        "name": "Head Branch",
                    }
                }
            ]
        )
        response = client.get(url_for(
            'main.api_future_events'
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        assert 'Test description draft event' not in page.find('p').text
        assert 'Test description approved event' in page.find('p').text


class WhenAccessingArticlesPage(object):

    def it_shows_list_of_articles(self, client, mocker, logged_in, sample_latest_magazine):
        mocker.patch(
            "app.clients.api_client.ApiClient.get_articles_summary",
            return_value=[
                {
                    "title": "Ancient Greece",
                    "author": "Julian Scott",
                    "short_content": "Some short info about something"
                }
            ]
        )

        response = client.get(url_for(
            'main.api_articles_summary'
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        assert page.select_one("#content p a").text == 'Ancient Greece'

    def it_shows_an_article(self, client, mocker, logged_in):
        article = {
            "id": str(uuid.uuid4()),
            "title": "Ancient Greece",
            "author": "Julian Scott",
            "content": "Something about how philosophy in Ancient Greece formed the bedrock of western philosophy"
        }

        mocker.patch(
            "app.clients.api_client.ApiClient.get_article",
            return_value=article
        )

        response = client.get(url_for(
            'main.api_article', id=article['id']
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        assert article['content'] in page.select_one("#content div").text
