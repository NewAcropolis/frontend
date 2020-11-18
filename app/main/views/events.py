# coding: utf-8
from datetime import datetime
from flask import request
from HTMLParser import HTMLParser

from app import api_client
from app.main import main
from app.main.views import render_page


@main.route('/events')
def events():
    articles = api_client.get_articles_summary()

    future_events = api_client.get_events_in_future(approved_only=True)

    for event in future_events:
        if event['venue']['name'] == 'Online Event':
            event['event_type'] = 'Online ' + event['event_type']

    past_events = []
    all_past_events = api_client.get_events_past_year()
    if all_past_events:
        while len(past_events) < 3 and all_past_events:
            event = all_past_events.pop(-1)
            if event['id'] not in [e['id'] for e in future_events]:
                if event['venue']['name'] == 'Online Event':
                    event['event_type'] = 'Online ' + event['event_type']

                past_events.append(event)

    return render_page(
        'views/events.html',
        articles=articles,
        future_events=future_events,
        past_events=past_events,
    )


@main.route('/event/<uuid:event_id>')
@main.route('/event_details/<uuid:event_id>')
@main.route('/event_details')
def event_details(event_id=None, **kwargs):
    if not event_id:
        event_id = request.args.get('eventid')
        if not event_id:
            return render_page(
                'errors/errors.html',
                message=['<h3>No event id set</h3>']
            )
        else:
            event = api_client.get_event_by_old_id(event_id)
    else:
        event = api_client.get_event_by_id(event_id)

    if not event:
        return render_page(
            'errors/errors.html',
            message=['<h3>No event found</h3>']
        )
    elif event['venue']['name'] == 'Online Event':
        event['event_type'] = 'Online ' + event['event_type']

    event['is_future_event'] = is_future_event(event)

    h = HTMLParser()
    event['_description'] = h.unescape(event['description'].encode('ascii', 'ignore'))

    return render_page(
        'views/event_details.html',
        event=event
    )


def is_future_event(event):
    for date in event['event_dates']:
        if date['event_datetime'] >= str(datetime.today()):
            return True
    return False
