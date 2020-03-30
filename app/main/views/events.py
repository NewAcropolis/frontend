from datetime import datetime
from random import randint
from app import api_client
from app.main import main
from app.main.views import render_page


@main.route('/whats-on')
def whats_on():
    articles = api_client.get_articles_summary()
    if articles:
        index = randint(0, len(articles) - 1)

    future_events = api_client.get_events_in_future(approved_only=True)
    past_events = []
    all_past_events = api_client.get_events_past_year()
    if all_past_events:
        while len(past_events) < 3:
            event = all_past_events.pop(-1)
            past_events.append(event)

    return render_page(
        'views/whats_on.html',
        current_page='whats-on',
        main_article=articles[index] if articles else None,
        articles=articles,
        future_events=future_events,
        past_events=past_events,
    )


@main.route('/event_details/<uuid:event_id>')
def event_details(event_id, **kwargs):
    event = api_client.get_event_by_id(event_id)
    event['is_future_event'] = is_future_event(event)

    return render_page(
        'views/event_details.html',
        event=event
    )


def is_future_event(event):
    is_future = False
    for date in event['event_dates']:
        if date['event_datetime'] >= str(datetime.today()):
            is_future = True
    return is_future
