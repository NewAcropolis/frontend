import pytest
from bs4 import BeautifulSoup
from flask import url_for


class WhenAccessingEventsPage(object):
    def it_should_show_header_logo_on_events_page(
        self, client, sample_future_events, sample_past_events_for_cards, sample_articles_summary
    ):
        response = client.get(url_for(
            'main.events'
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        header_image = page.find('img')['src']
        assert header_image == '/static/images/NALogo25a.png'

    def it_should_show_in_events_past_and_future_events_in_cards(
        self, mocker, client,
        sample_articles_summary, sample_future_event_for_cards, sample_past_events_for_cards, sample_marketings,
        sample_latest_magazine
    ):
        mocker.patch('app.main.views.index.api_client.get_events_in_future', return_value=sample_future_event_for_cards)
        mocker.patch('app.main.views.index.api_client.get_events_past_year', return_value=sample_past_events_for_cards)
        response = client.get(url_for(
            'main.events'
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')

        past_events = page.findAll("div", {"class": "past_corner"})
        future_events = page.findAll("div", {"id": "future_event"})

        assert len(past_events) == 3
        assert len(future_events) == 1

    def it_should_show_giant_past_event(
        self, mocker, client, sample_articles_summary, sample_future_event_for_cards, sample_past_events_for_cards,
        sample_latest_magazine
    ):
        mocker.patch('app.main.views.index.api_client.get_events_in_future', return_value=sample_future_event_for_cards)
        mocker.patch('app.main.views.index.api_client.get_events_past_year', return_value=sample_past_events_for_cards)
        response = client.get(url_for(
            'main.events'
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')

        giant_past_event = page.findAll("div", {"class": "giant_past_corner"})

        assert len(giant_past_event) == 1

    @pytest.mark.parametrize('div_class', ['#navbarNav', '.footnav'])
    def it_shows_list_of_available_pages_on_header_and_footer(
        self, client, sample_future_events, sample_articles_summary, div_class
    ):
        expected_link_text = ['About', 'Courses', 'Events', 'Magazines', 'Shop']
        response = client.get(url_for(
            'main.events'
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')

        selected_div = page.select_one(div_class)

        for i, li in enumerate(selected_div.select('li a')):
            assert li.text == expected_link_text[i]


class WhenAccessingEventsDetailsPage(object):
    def it_shows_an_event_detail(self, mocker, client, sample_future_event, sample_latest_magazine):
        mocker.patch('app.main.views.index.api_client.get_event_by_id', return_value=sample_future_event)

        response = client.get(url_for(
            'main.event_details',
            event_id=sample_future_event['id']
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        title = page.select_one('.event_title')

        assert title.text == sample_future_event['title']

    def it_shows_an_event_detail_for_legacy_links(self, mocker, client, sample_future_event, sample_latest_magazine):
        mocker.patch('app.main.views.index.api_client.get_event_by_old_id', return_value=sample_future_event)

        response = client.get(url_for(
            'main.event_details',
            eventid=sample_future_event['id']
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        title = page.select_one('.event_title')

        assert title.text == sample_future_event['title']

    def it_shows_an_error_message_when_no_event_id(self, mocker, client, sample_latest_magazine):
        response = client.get(url_for(
            'main.event_details'
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        message = page.select_one('#content h3')

        assert message.text == 'No event id set'

    def it_shows_an_error_message_when_event_not_found(self, mocker, client, sample_latest_magazine):
        mocker.patch('app.main.views.index.api_client.get_event_by_old_id', return_value=None)
        response = client.get(url_for(
            'main.event_details',
            eventid='1'
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        message = page.select_one('#content h3')

        assert message.text == 'No event found'
