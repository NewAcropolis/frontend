from datetime import datetime, timedelta
from app.clients.api_client import ApiClient


class WhenGettingNiceEventDate:

    def it_gets_nice_event_date(self, app, sample_future_events):
        api_client = ApiClient()
        future_dates = []
        for n in range(3):
            d = datetime.strftime(datetime.now() + timedelta(days=n + 1), "%a %-d of %B - 7 PM")
            if 'Tue' in d:
                d = d.replace('Tue', 'Tues')
            elif 'Thu' in d:
                d = d.replace('Thu', 'Thurs')
            future_dates.append(d)

        nice_dates = api_client.get_nice_event_dates(sample_future_events)
        assert nice_dates[0]['formatted_event_datetimes'] == future_dates[0]
        assert not nice_dates[0]['end_time']
        assert nice_dates[0]['event_time'] == '19:00'
        assert nice_dates[1]['formatted_event_datetimes'] == future_dates[1]
        assert nice_dates[1]['end_time'] == "20:30"
        assert nice_dates[2]['formatted_event_datetimes'] == future_dates[2]
        assert not nice_dates[2]['end_time']
