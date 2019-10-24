from flask import url_for
from bs4 import BeautifulSoup
from mock import call


class WhenSubmittingSubscriptionForm(object):
    def it_displays_the_submitted_email(
        self, client, mocker, sample_future_events, sample_articles_summary, sample_marketings
    ):
        response = client.post(
            url_for('main.index'),
            data={
                'subscription_email': 'test@test.com',
            },
            follow_redirects=True
        )

        assert response.status_code == 200

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        submitted_email = page.select_one('#subscription_email')

        assert submitted_email.attrs['value'] == "test@test.com"

    def it_shows_validation_error_when_empty(
        self, client, mocker, sample_future_events, sample_articles_summary, sample_marketings
    ):
        response = client.post(
            url_for('main.index'), follow_redirects=True
        )

        assert response.status_code == 200

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        error = page.find("div", {"class": "error_text"}).text.strip()

        assert error == "This field is required."

    def it_shows_validation_for_invalid_email(
        self, client, mocker, sample_future_events, sample_articles_summary, sample_marketings
    ):
        response = client.post(
            url_for('main.subscription', email='test@test.com'),
            data={
                'subscription_name': 'Test',
                'subscription_email': 'test',
                'subscription_marketings': sample_marketings[0]['id']
            }
        )

        assert response.status_code == 200

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        error = page.find("div", {"class": "error_text"}).text.strip()

        assert error == "Invalid email address."

    def it_shows_error_on_failed_submit_to_api(
        self, client, mocker, sample_future_events, sample_articles_summary, sample_marketings
    ):
        mocker.patch(
            'app.main.views.subscription.api_client.add_subscription_email',
            side_effect=Exception('API error')
        )

        response = client.post(
            url_for('main.subscription', email='test@test.com'),
            data={
                'subscription_name': 'Test',
                'subscription_email': 'test@test.com',
                'subscription_marketings': sample_marketings[0]['id']
            }
        )

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        error = page.find("div", {"class": "error_text"}).text.strip()
        assert error == "Failed to process email, please try again later"

    def it_submits_to_api(self, client, mocker, sample_future_events, sample_articles_summary, sample_marketings):

        mocked_add_subscription_email = mocker.patch('app.main.views.subscription.api_client.add_subscription_email')

        response = client.post(
            url_for('main.subscription', email='test@test.com'),
            data={
                'subscription_name': 'Test',
                'subscription_email': 'test@test.com',
                'subscription_marketings': sample_marketings[0]['id']
            }
        )

        assert response.status_code == 200

        assert mocked_add_subscription_email.call_args == call(
            'Test', 'test@test.com', sample_marketings[0]['id']
        )
