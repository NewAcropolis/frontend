from datetime import datetime

from na_common.dates import get_nice_event_dates as common_get_nice_event_dates


def get_nice_event_dates(events, future_dates_only=False):
    for event in events:
        if future_dates_only:
            event['event_dates'] = get_future_event_dates(event['event_dates'])
        print(event)
        event = get_nice_event_date(event)
    return events


def get_nice_event_date(event):
    event['formatted_event_datetimes'] = common_get_nice_event_dates(event['event_dates'])
    event['dates'] = get_event_dates(event['event_dates'])

    event_date = event["event_dates"][0]
    _datetime = datetime.strptime(event_date["event_datetime"], '%Y-%m-%d %H:%M')
    if event['event_type'] == 'Introductory Course':
        event['event_monthyear'] = _datetime.strftime('%B %Y')

    event_date['event_time'] = _datetime.strftime('%H:%M')
    if not event.get('event_time'):
        event['event_time'] = event_date['event_time']
    else:
        if _datetime.minute > 0:
            time = _datetime.strftime('%-I:%M %p')
        else:
            time = _datetime.strftime('%-I %p')
        event['event_time'] = time
    if not event.get('end_time'):
        event['end_time'] = event_date["end_time"]

    return event


def get_future_event_dates(event_dates):
    future_dates = []
    for event_date in event_dates:
        _datetime = datetime.strptime(event_date["event_datetime"], '%Y-%m-%d %H:%M')
        if _datetime >= datetime.today():
            future_dates.append(event_date)

    return future_dates


def get_event_dates(event_dates):
    dates = []
    for event_date in event_dates:
        _datetime = datetime.strptime(event_date["event_datetime"], '%Y-%m-%d %H:%M')
        dates.append(_datetime.strftime('%Y-%m-%d'))

    return dates
