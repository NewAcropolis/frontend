from datetime import datetime
from flask import request
from random import randint
from app import api_client
from app.main import main
from app.main.views import render_page


@main.route('/events')
def events():
    articles = api_client.get_articles_summary()
    if articles:
        index = randint(0, len(articles) - 1)

    future_events = api_client.get_events_in_future(approved_only=True)
    past_events = []
    all_past_events = api_client.get_events_past_year()
    if all_past_events:
        while len(past_events) < 3 and all_past_events:
            event = all_past_events.pop(-1)
            past_events.append(event)

    return render_page(
        'views/events.html',
        main_article=articles[index] if articles else None,
        articles=articles,
        future_events=future_events,
        past_events=past_events,
    )


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

    event['is_future_event'] = is_future_event(event)

    return render_page(
        'views/event_details.html',
        event=event
    )


def is_future_event(event):
    for date in event['event_dates']:
        if date['event_datetime'] >= str(datetime.today()):
            return True
    return False
