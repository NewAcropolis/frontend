import json
from datetime import datetime, timedelta
from flask import current_app, jsonify, redirect, render_template, request, session, url_for

from app import api_client
from app.clients.errors import HTTPError
from app.main import main
from app.main.forms import EmailForm


@main.route('/admin/emails', methods=['GET', 'POST'])
@main.route('/admin/emails/<uuid:selected_email_id>', methods=['GET', 'POST'])
@main.route('/admin/events/<uuid:selected_event_id>/<api_message>', methods=['GET', 'POST'])
def admin_emails(selected_email_id=None, api_message=None):
    future_emails = api_client.get_future_emails()
    email_types = api_client.get_email_types()
    future_events = api_client.get_events_in_future()

    session['emails'] = future_emails
    session['future_events'] = future_events

    errors = []
    form = EmailForm()

    form.set_emails_form(future_emails, email_types, future_events)

    if form.validate_on_submit():
        email = {
            'email_id': form.emails.data,
            'event_id': form.events.data,
            'details': form.details.data,
            'extra_txt': form.extra_txt.data,
            'email_state': form.email_state.data,
            'email_type': form.email_types.data,
            'send_starts_at': form.send_starts_at.data,
            'expires': form.expires.data,
        }

        try:
            message = None
            if email.get('email_id'):
                if form.email_types.data == 'event' and not email['event_id']:
                    emails = [e for e in future_emails if e['id'] == form.emails.data]
                    if emails:
                        email['event_id'] = emails[0]['event_id']

                if email['email_state'] == 'rejected':
                    email['reject_reason'] = form.reject_reason.data

                response = api_client.update_email(email['email_id'], email)
                message = 'email updated'
            else:
                del email['email_id']
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
    email = [e for e in session['emails'] if e['id'] == request.args.get('email')]
    if email:
        return jsonify(email[0])
    return ''


@main.route('/admin/_get_event_dates')
def _get_event_dates():
    event = [e for e in session['future_events'] if e['id'] == request.args.get('event')]
    if event:
        first_event_date = event[0]['event_dates'][0]['event_datetime'].split(' ')[0]
        send_starts_at = datetime.strptime(first_event_date, '%Y-%m-%d') - timedelta(weeks=2)
        last_event_date = event[0]['event_dates'][-1]['event_datetime'].split(' ')[0]
        return jsonify({
            'send_starts_at': send_starts_at.strftime('%Y-%m-%d'),
            'last_event_date': last_event_date
        })
    return ''
