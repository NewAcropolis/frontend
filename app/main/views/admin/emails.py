# coding: utf-8
import json
from datetime import datetime, timedelta
from flask import current_app, jsonify, redirect, render_template, request, session, url_for

from app import api_client
from app.clients.errors import HTTPError
from app.main import main
from app.main.forms import EmailForm
from app.queue import Queue


@main.route('/admin/emails', methods=['GET', 'POST'])
@main.route('/admin/emails/magazine/<uuid:magazine_id>', methods=['GET', 'POST'])
@main.route('/admin/emails/<string:selected_email_id>', methods=['GET', 'POST'])
@main.route('/admin/emails/<string:selected_email_id>/<api_message>', methods=['GET', 'POST'])
def admin_emails(selected_email_id=None, magazine_id=None, api_message=None):
    errors = []

    future_emails = api_client.get_pending_and_latest_emails()
    session['emails'] = future_emails
    future_events = api_client.get_events_in_future(approved_only=True)
    session['future_events'] = future_events

    email_types = api_client.get_email_types()
    if magazine_id:
        for e in [fe for fe in future_emails if 'magazine_id' in fe]:
            if e['magazine_id'] == str(magazine_id):
                selected_email_id = e['id']

        if not selected_email_id:
            errors = "No matching magazine email found"

    form = EmailForm()

    form.set_emails_form(future_emails, email_types, future_events)

    if form.events.data not in [k for k, v in form.events.choices]:
        form.events.data = None

    if form.validate_on_submit():
        subject = ''
        email = {
            'id': form.emails.data,
            'details': form.details.data,
            'extra_txt': form.extra_txt.data,
            'email_state': form.email_state.data,
            'email_type': form.email_types.data,
            'send_starts_at': form.send_starts_at.data,
            'expires': form.expires.data,
        }

        if form.email_types.data == 'event':
            for k, v in form.events.choices:
                if k == form.events.data:
                    subject = v

            email.update(event_id=form.events.data)
        elif form.email_types.data == 'basic':
            email.update(extra_txt=form.basic_content.data)
            subject = form.subject.data

        email.update(subject=subject)

        try:
            message = None
            if email.get('id'):
                if form.email_types.data == 'event' and not email['event_id']:
                    emails = [e for e in future_emails if e['id'] == form.emails.data]
                    if emails:
                        email['event_id'] = emails[0]['event_id']
                elif form.email_types.data == 'basic':
                    email['subject'] = form.subject.data
                    email['extra_txt'] = form.basic_content.data
                elif form.email_types.data == 'magazine' and 'magazine_id' not in email:
                    emails = [e for e in future_emails if e['id'] == form.emails.data]
                    if emails:
                        email['subject'] = emails[0]['subject']
                        email['magazine_id'] = emails[0]['magazine_id']

                if email['email_state'] == 'rejected':
                    email['reject_reason'] = form.reject_reason.data

                response = api_client.update_email(email['id'], email)
                message = 'email updated'
            else:
                del email['id']
                response = api_client.add_email(email)

            current_app.logger.info('Submit email: {}, {}'.format(email, response))

            return redirect(url_for('main.admin_emails', selected_email_id=response['id'], api_message=message))
        except HTTPError as e:
            current_app.logger.error(e)
            errors = json.dumps(e.message)

    return render_template(
        'views/admin/emails.html',
        selected_email_id=selected_email_id,
        message=api_message,
        form=form,
        errors=errors
    )


@main.route('/admin/_get_email')
def _get_email():
    _email = [e for e in session['emails'] if e['id'] == request.args.get('email')]
    if _email:
        email = _email[0]
        if email['email_type'] == 'event':
            event = [e for e in session['future_events'] if e['id'] == request.args.get('event')]
            if not event:
                event = api_client.get_event_by_id(email['event_id'])

                event_dates = [e['event_datetime'][5:-6] for e in event['event_dates']]
                parts = [
                    "{}/{}".format(date_parts[1].lstrip('0'), date_parts[0].lstrip('0'))
                    for date_parts in [date.split('-') for date in event_dates]
                ]

                email['event'] = {
                    'value': event['id'],
                    'text': u'{} - {} - {}'.format(
                        ", ".join(parts),
                        event['event_type'],
                        event['title']
                    ),
                    'has_expired': event['has_expired']
                }
        elif email['email_type'] == 'magazine':
            magazine = api_client.get_magazine(email['magazine_id'])
            email['magazine'] = {
                'title': magazine['title'],
                'filename': magazine['filename'],
            }

        if 'emails_sent_counts' not in email:
            email['emails_sent_counts'] = {
                "success": 0,
                "failed": 0,
                "total_active_members": "N/A"
            }

        if email.get('pending'):
            q_item = Queue.get_item_by_payload_key('pending_emails', 'id', email['id'])
            email['held_until'] = Queue.hold_off_processing(q_item).strftime('%-I:%M %p')

        return jsonify(email)
    return ''


@main.route('/admin/_get_event_dates/<date_type>')
def _get_event_dates(date_type):
    if 'event' in request.args:
        event = [e for e in session['future_events'] if e['id'] == request.args.get('event')]
    elif 'future_events' in session:
        event = [session['future_events'][0]]
    if event:
        if date_type == 'send':
            first_event_date = event[0]['event_dates'][0]['event_datetime'].split(' ')[0]
            send_starts_at = datetime.strptime(first_event_date, '%Y-%m-%d') - timedelta(weeks=2)
            return jsonify({
                'send_starts_at': send_starts_at.strftime('%Y-%m-%d'),
            })
        elif date_type == 'last':
            last_event_date = event[0]['event_dates'][-1]['event_datetime'].split(' ')[0]
            return jsonify({
                'last_event_date': last_event_date
            })
    return ''


@main.route('/admin/_get_default_details')
def _get_default_details():
    event = [e for e in session['future_events'] if e['id'] == request.args.get('event')]

    if not event:
        return ''

    event = event[0]

    details = u"<div><strong>Fees:</strong> £{}, £{} concession for students, "\
        u"income support &amp; OAPs, and free for members of New Acropolis.</div><div><strong>Venue:</strong> "\
        u"{}</div>{}".format(event['fee'], event['conc_fee'], event['venue']['address'], event['venue']['directions'])

    return jsonify({'details': details})


@main.route('/admin/_cancel_pending_email')
def _cancel_pending_email():
    email_id = request.args.get('email')
    if email_id:
        api_client.cancel_pending_email(email_id)

    return redirect(f"{url_for('main.admin_emails')}/" + email_id)
