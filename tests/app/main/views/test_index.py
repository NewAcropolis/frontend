import pytest
from bs4 import BeautifulSoup
from flask import url_for


class WhenAccessingHomePage(object):
    def it_should_show_header_logo(self, client, sample_future_events, sample_articles_summary):
        response = client.get(url_for(
            'main.index'
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        header_image = page.find('img')['src']
        assert header_image == '/static/images/NALogo25.png'

    def it_should_show_future_events_in_carousel(self, client, sample_future_events, sample_articles_summary):
        response = client.get(url_for(
            'main.index'
        ))

        other_events = []
        for event in sample_future_events:
            if event['event_type'] != 'Introductory Course':
                other_events.append(event)

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        carousel_title = page.select(".carousel-title")
        for i, event in enumerate(sample_future_events):
            if event['event_type'] == 'Introductory Course':
                # expect the first event in the carousel to be an intro course
                assert carousel_title[0].text.strip() == "Test title 3"
            elif event['image_filename']:
                # expect the other events to be after an intro course if they have an image
                assert carousel_title[i + 1].text.strip() == other_events[i]['title']

    def it_should_show_future_events_in_cards(self, client, sample_future_events, sample_articles_summary):
        response = client.get(url_for(
            'main.index'
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        content = page.find("p", {"class": "card-text cardtextmulti dark_grey_txt"}).string

        intro_course = [e for e in sample_future_events if e['event_type'] == 'Introductory Course'][0]

        assert content == intro_course['title']

    def it_should_show_past_and_future_events_in_cards(
        self, mocker, client, sample_articles_summary, sample_future_event_for_cards, sample_past_events_for_cards,
        sample_latest_magazine
    ):
        mocker.patch('app.main.views.index.api_client.get_events_in_future', return_value=sample_future_event_for_cards)
        mocker.patch('app.main.views.index.api_client.get_events_past_year', return_value=sample_past_events_for_cards)
        response = client.get(url_for(
            'main.index'
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')

        content = page.findAll("div", {"class": "past_corner"})
        assert len(content) == 2

    def it_should_display_text_for_main_article(self, mocker, client, sample_future_events, sample_articles_summary):
        # store values here as the random article index is always removed
        sample_title = sample_articles_summary[0]['title']
        sample_content = sample_articles_summary[0]['short_content']
        mocker.patch('app.main.views.index.randint', return_value=0)
        response = client.get(url_for(
            'main.index'
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        title = page.select_one("#main_article h2").text
        content = page.select_one("#main_article p").text
        assert title == sample_title
        assert content == sample_content + " READ MORE"

    def it_should_show_featured_articles_in_cards(self, client, sample_future_events, sample_articles_summary):
        response = client.get(url_for(
            'main.index'
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        article_title = page.find("h4", {"id": "article_1"}).string

        assert article_title == sample_articles_summary[0]['title']

    @pytest.mark.parametrize('div_class', ['#navbarNav', '.footnav'])
    def it_shows_list_of_available_pages_on_header_and_footer(
        self, client, sample_future_events, sample_articles_summary, div_class
    ):
        expected_link_text = ['About', 'Courses', 'Events', 'Magazines', 'Shop']
        response = client.get(url_for(
            'main.index'
        ))
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')

        selected_div = page.select_one(div_class)

        for i, li in enumerate(selected_div.select('li a')):
            assert li.text == expected_link_text[i]
