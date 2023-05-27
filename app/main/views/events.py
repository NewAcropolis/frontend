# coding: utf-8
from datetime import datetime
from flask import current_app, jsonify, request, session
from html import unescape

import pytz

from app import api_client
from app.clients.errors import HTTPError
from app.main import main
from app.main.forms import ReservePlaceForm
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
    event['is_paypal_ready'] = is_paypal_ready(event)
    event['date_ids'] = [str(e['id']) for e in event['event_dates']]
    event['accept_donation'] = event["fee"] == -3
    event['show_buy_now'] = event["fee"] and event["fee"] not in [-3, -1]

    event['_description'] = unescape(event['description'])

    reserve_place_form = ReservePlaceForm() if event['is_future_event'] and\
        event['event_type'] == 'Introductory Course' else None

    return render_page(
        'views/event_details.html',
        event=event,
        reserve_place_form=reserve_place_form
    )


def is_future_event(event):
    for date in event['event_dates']:
        if date['event_datetime'] >= str(datetime.today()):
            return True
    return False


def is_paypal_ready(event):
    return event['booking_code'] and not event['booking_code'].startswith('pending:')


@main.route('/_reserve_place', methods=['GET', 'POST'])
def _reserve_place():
    reserve_place_form = ReservePlaceForm()

    reserve_place_form.validate()

    if reserve_place_form.validate_on_submit():
        current_app.logger.info(
            'reserve_place: %s, %s, %s',
            reserve_place_form.reserve_place_name.data,
            reserve_place_form.reserve_place_email.data,
            reserve_place_form.reserve_place_date_id.data,
        )
        try:
            resp = api_client.reserve_place(
                name=reserve_place_form.reserve_place_name.data,
                email=reserve_place_form.reserve_place_email.data,
                eventdate_id=reserve_place_form.reserve_place_date_id.data,
            )
            if 'error' in session:
                error = session.pop('error')
                current_app.logger.error(error)
                tz = pytz.timezone("Europe/London")
                return jsonify(
                    {'error': 'Problem reserving a place at {}, please try again later'.format(
                        datetime.now(tz).strftime('%H:%M:%S %d/%m/%y'))}
                )
            else:
                return jsonify(resp)
        except HTTPError as e:
            return jsonify({'error': e.message})
    return jsonify({'errors': reserve_place_form.errors})
