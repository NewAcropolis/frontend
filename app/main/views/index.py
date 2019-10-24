from datetime import datetime
from flask import current_app, jsonify, session
import pytz
from random import randint
from app import api_client
from app.main import main
from app.main.views import render_page
from six.moves.html_parser import HTMLParser
from app.main.forms import ContactForm
from app.clients.errors import HTTPError


@main.route('/', methods=['GET', 'POST'])
def index():
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

    return render_page(
        'views/home.html',
        main_article=main_article,
        articles=articles,
        all_events=all_events,
        current_page=''
    )


@main.route('/about')
def about():
    return render_page('views/about.html')


@main.route('/resources')
def resources():
    return render_page('views/resources.html')


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


@main.route('/what-we-offer')
def what_we_offer():
    return render_page('views/what_we_offer.html')


@main.route('/e-shop')
def e_shop():
    return render_page('views/e-shop.html')


@main.route('/course_details')
def course_details():
    return render_page('views/course_details.html')


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


def _unescape_html(items, field_name):
    h = HTMLParser()
    for item in items:
        item[field_name] = h.unescape(item[field_name])

    return items


@main.route('/_send_message', methods=['GET', 'POST'])
def _send_message():
    contact_form = ContactForm()
    contact_form.setup()

    if contact_form.validate_on_submit():
        current_app.logger.info(
            'send_message: %s, %s, %s, %s',
            contact_form.contact_name.data,
            contact_form.contact_email.data,
            contact_form.contact_reasons.data,
            contact_form.contact_message.data
        )
        try:
            resp = api_client.send_message(
                name=contact_form.contact_name.data,
                email=contact_form.contact_email.data,
                reason=contact_form.contact_reasons.data,
                message=contact_form.contact_message.data
            )
            if 'error' in session:
                error = session.pop('error')
                current_app.logger.error(error)
                tz = pytz.timezone("Europe/London")
                return jsonify(
                    {'error': 'Problem sending message at {}, please try again later'.format(
                        datetime.now(tz).strftime('%H:%M:%S %d/%m/%y'))}
                )
            else:
                return jsonify(resp)
        except HTTPError as e:
            return jsonify({'error': e.message})
    return jsonify({'errors': contact_form.errors})
