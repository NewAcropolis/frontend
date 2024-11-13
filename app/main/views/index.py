from datetime import datetime
from flask import current_app, jsonify, session
import pytz
from random import randint
from app import api_client
from app.main import main
from app.main.views import render_page
from html import unescape
from app.main.forms import ContactForm
from app.clients.errors import HTTPError


@main.route('/', methods=['GET', 'POST'])
def index():
    future_events = api_client.get_events_in_future(approved_only=True)

    for event in future_events:
        if event['event_type'] == 'Introductory Course':
            event['carousel_text'] = 'Courses starting {}'.format(event['event_monthyear'])
        if event['venue']['name'] == 'Online Event':
            event['event_type'] = 'Online ' + event['event_type']
    # breakpoint()
    articles = api_client.get_articles_summary_by_tags()
    if articles:
        index = randint(0, len(articles) - 1)
        main_article = articles[index]
        del articles[index]
    else:
        main_article = ''

    all_events = future_events
    if len(all_events) < 3:
        past_events = api_client.get_events_past_year()
        if past_events:
            while len(all_events) < 3 and past_events:
                event = past_events.pop(-1)
                if event['id'] not in [e['id'] for e in future_events]:
                    event['past'] = True
                    all_events.append(event)
    return render_page(
        'views/home.html',
        main_article=main_article,
        articles=articles,
        all_events=all_events[:4]
    )


@main.route('/about')
def about():
    return render_page('views/about.html')


def _unescape_html(items, field_name):
    for item in items:
        item[field_name] = unescape(item[field_name])

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
