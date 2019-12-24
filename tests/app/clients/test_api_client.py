from app.clients.api_client import ApiClient


class WhenGettingNiceEventDate:

    def it_gets_nice_event_date(self, app, sample_future_events):
        api_client = ApiClient()
        nice_dates = api_client.get_nice_event_dates(sample_future_events)
        assert nice_dates[0]['formatted_event_datetimes'] == "Sun 30 of December - 7 PM"
        assert not nice_dates[0]['end_time']
        assert nice_dates[0]['event_time'] == '19:00'
        assert nice_dates[1]['formatted_event_datetimes'] == "Mon 31 of December - 7 PM"
        assert nice_dates[1]['end_time'] == "20:30"
        assert nice_dates[2]['formatted_event_datetimes'] == "Tue 1 of January - 7 PM"
        assert not nice_dates[2]['end_time']
