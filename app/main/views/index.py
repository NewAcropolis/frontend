from datetime import datetime
from flask import render_template
from random import randint
from app.main import main
from app import api_client
from app.main.decorators import setup_subscription_form
from six.moves.html_parser import HTMLParser


@main.route('/', methods=['GET', 'POST'])
@setup_subscription_form
def index(**kwargs):
    future_events = api_client.get_events_in_future(approved_only=True)
    for event in future_events:
        if event['event_type'] == 'Introductory Course':
            event['carousel_text'] = 'Courses starting {}'.format(event['event_monthyear'])

    articles = api_client.get_articles_summary()
    if articles:
        index = randint(0, len(articles) - 1)
        main_article = articles[index]
    else:
        main_article = ''

    all_events = future_events
    if len(all_events) < 3:
        past_events = api_client.get_events_past_year()
        if past_events:
            while len(all_events) < 3:
                event = past_events.pop(-1)
                event['past'] = True
                all_events.append(event)

    return render_template(
        'views/home.html',
        main_article=main_article,
        articles=articles,
        all_events=all_events,
        current_page='',
        **kwargs
    )


@main.route('/about')
@setup_subscription_form
def about(**kwargs):
    return render_template(
        'views/about.html',
        current_page='about',
        **kwargs
    )


@main.route('/resources')
@setup_subscription_form
def resources(**kwargs):
    return render_template(
        'views/resources.html',
        current_page='resources',
        **kwargs
    )


@main.route('/whats-on')
@setup_subscription_form
def whats_on(**kwargs):
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

    return render_template(
        'views/whats_on.html',
        current_page='whats-on',
        main_article=articles[index] if articles else None,
        articles=articles,
        future_events=future_events,
        past_events=past_events,
        **kwargs
    )


@main.route('/what-we-offer')
@setup_subscription_form
def what_we_offer(**kwargs):
    return render_template(
        'views/what_we_offer.html',
        current_page='what-we-offer',
        **kwargs
    )


@main.route('/e-shop')
@setup_subscription_form
def e_shop(**kwargs):
    return render_template(
        'views/e-shop.html',
        current_page='e-shop',
        **kwargs
    )


@main.route('/course_details')
@setup_subscription_form
def course_details(**kwargs):
    return render_template(
        'views/course_details.html',
        **kwargs
    )


@main.route('/event_details/<uuid:event_id>')
@setup_subscription_form
def event_details(event_id, **kwargs):
    event = api_client.get_event_by_id(event_id)
    event['is_future_event'] = is_future_event(event)

    return render_template(
        'views/event_details.html',
        event=event,
        **kwargs
    )


def is_future_event(event):
    is_future = False
    for date in event['event_dates']:
        if date['event_datetime'] >= str(datetime.today()):
            is_future = True
    return is_future


def _unescape_html(items, field_name):
    h = HTMLParser()
    for item in items:
        item[field_name] = h.unescape(item[field_name])

    return items
