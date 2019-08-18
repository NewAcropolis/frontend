from flask import current_app, render_template, request
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
    index = randint(0, len(articles) - 1)

    all_events = future_events
    if len(all_events) < 3:
        past_events = api_client.get_events_past_year()

        while len(all_events) < 3:
            event = past_events.pop(-1)
            event['past'] = True
            all_events.append(event)

    return render_template(
        'views/home.html',
        images_url=current_app.config['IMAGES_URL'],
        main_article=articles[index],
        articles=articles,
        all_events=all_events,
        current_page='',
        **kwargs
    )


@main.route('/about')
@setup_subscription_form
def about(**kwargs):
    events = api_client.get_events_in_future(approved_only=True)
    for event in events:
        if event['event_type'] == 'Introductory Course':
            event['carousel_text'] = 'Courses starting {}'.format(event['event_monthyear'])

    articles = api_client.get_articles_summary()
    index = randint(0, len(articles) - 1)
    return render_template(
        'views/about.html',
        images_url=current_app.config['IMAGES_URL'],
        main_article=articles[index],
        articles=articles,
        events=events,
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
    return render_template(
        'views/whats_on.html',
        current_page='whats-on',
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


@main.route('/event_details')
@setup_subscription_form
def event_details(**kwargs):
    events = api_client.get_events_in_future(approved_only=True)
    event_details = request.args.get('event_details')
    future_events = api_client.get_events_in_future(approved_only=True)
    past_events = api_client.get_events_past_year()
    all_events = future_events + past_events
    displayed_event = []
    for event in all_events:
        if event_details == event['title']:
            displayed_event = event

    return render_template(
        'views/event_details.html',
        images_url=current_app.config['IMAGES_URL'],
        displayed_event=displayed_event,
        events=_unescape_html(events, 'description'),
        paypal_account=current_app.config['PAYPAL_ACCOUNT'],
        **kwargs
    )


def _unescape_html(items, field_name):
    h = HTMLParser()
    for item in items:
        item[field_name] = h.unescape(item[field_name])

    return items
