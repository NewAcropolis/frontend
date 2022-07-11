import base64
from flask import current_app, jsonify, redirect, render_template, request, session, url_for
from six.moves.html_parser import HTMLParser
import json
import urllib.parse as urlparse

from app import api_client
from app.cache import Cache
from app.clients.api_client import only_show_approved_events, update_cache
from app.clients.errors import HTTPError
from app.main import main
from app.main.forms import EventAttendanceForm, EventForm
from app.main.views import render_page
from app.main.views.events import is_future_event

from na_common.dates import get_nice_event_dates as common_get_nice_event_dates


def is_admin_user():
    user = session['user']
    return 'admin' in user.get('access_area') or user.get('access_area') == 'admin'


def size_from_b64(b64string):
    return float(len(b64string) * 3) / 4 - b64string.count('=', -2)


@main.route('/admin/events', methods=['GET', 'POST'])
@main.route('/admin/events/<uuid:selected_event_id>', methods=['GET', 'POST'])
@main.route('/admin/events/<uuid:selected_event_id>/<api_message>', methods=['GET', 'POST'])
def admin_events(selected_event_id=None, api_message=None):
    events = api_client.get_limited_events()
    event_types = api_client.get_event_types()
    speakers = api_client.get_speakers()
    venues = api_client.get_venues()
    session['events'] = events
    form = EventForm()

    temp_event = None
    errors = reject_reasons = []

    form.set_events_form(events, event_types, speakers, venues)

    if form.validate_on_submit():
        if form.image_filename.data:
            filename = form.image_filename.data.filename
        else:
            filename = form.existing_image_filename.data

        reject_reasons = json.loads(form.reject_reasons_json.data)

        if form.reject_reason.data:
            reject_reasons.append(
                {
                    'reason': form.reject_reason.data,
                    'created_by': session['user']['id']
                }
            )

        event = {
            'event_id': form.events.data,
            'event_type_id': form.event_type.data,
            'title': form.title.data,
            'sub_title': form.sub_title.data,
            'description': form.description.data,
            'image_filename': filename,
            'fee': int(form.fee.data) if form.fee.data else 0,
            'conc_fee': int(form.conc_fee.data) if form.conc_fee.data else 0,
            'multi_day_fee': int(form.multi_day_fee.data) if form.multi_day_fee.data else 0,
            'multi_day_conc_fee': int(form.multi_day_conc_fee.data) if form.multi_day_conc_fee.data else 0,
            'venue_id': form.venue.data,
            'event_dates': form.event_dates.data,
            'start_time': form.start_time.data,
            'end_time': form.end_time.data,
            'event_state': form.submit_type.data,
            'reject_reasons': reject_reasons,
            'remote_access': form.remote_access.data,
            'remote_pw': form.remote_pw.data,
            'show_banner_text': form.show_banner_text.data
        }

        adjusted_event = event.copy()

        from html import escape
        adjusted_event['description'] = escape(event['description'])
        adjusted_event['event_dates'] = json.loads(str(event['event_dates']))
        file_request = request.files.get('image_filename')
        if file_request:
            file_data = file_request.read()
            file_data_encoded = base64.b64encode(file_data)
            file_data_encoded = base64.b64encode(file_data_encoded).decode('utf-8')
            _file_size = size_from_b64(str(file_data_encoded))
            if _file_size > current_app.config['MAX_IMAGE_SIZE']:
                _file_size_mb = round(_file_size/(1024*1024), 1)
                _max_size_mb = current_app.config['MAX_IMAGE_SIZE']/(1024*1024)
                errors.append("Image {} file size ({} mb) is larger than max ({} mb)".format(
                    file_request.filename, _file_size_mb, _max_size_mb))
            else:
                adjusted_event['image_data'] = file_data_encoded

        if not errors:
            # remove empty values
            for key, value in event.items():
                if value != 0 and not value:
                    del adjusted_event[key]

            try:
                message = None
                if event.get('event_id'):
                    response = api_client.update_event(event['event_id'], adjusted_event)
                    message = 'event updated'

                    if event['event_state'] != "approved" and not form.cache_switch.data:
                        Cache.set_review_entity('get_events_in_future', event.get('event_id'))
                    else:
                        Cache.delete_review_entity('get_events_in_future', event.get('event_id'))
                        update_cache(
                            func=api_client.get_events_in_future_from_db,
                            decorator=only_show_approved_events, approved_only=True)
                else:
                    # do not need to update the cache here as an event is never in approved state when first created
                    response = api_client.add_event(adjusted_event)

                if 'error' in session:
                    raise HTTPError(response, message=session.pop('error'))

                return redirect(url_for('main.admin_events', selected_event_id=response.get('id'), api_message=message))
            except HTTPError as e:
                current_app.logger.error(e)
                temp_event = json.dumps(event)
                if "message" in e.message:
                    errors = e.message['message']
                else:
                    errors = json.dumps(e.message)

    return render_template(
        'views/admin/events.html',
        form=form,
        images_url=current_app.config['IMAGES_URL'],
        selected_event_id=selected_event_id,
        message=api_message,
        temp_event=temp_event,
        errors=json.dumps(errors)
    )


@main.route('/admin/events/attendance/<int:year>/<uuid:eventdate_id>', methods=['GET', 'POST'])
@main.route('/admin/events/attendance/<int:year>', methods=['GET', 'POST'])
@main.route('/admin/events/attendance', methods=['GET', 'POST'])
def events_attendance(eventdate_id=None, year=None):
    events = api_client.get_events_in_year(year)
    attendance_form = EventAttendanceForm()

    attendance_form.setup_form(year, events, eventdate_id)

    if not eventdate_id and events:
        eventdate_id = events[0]['event_dates'][0]['id']
    event_attendance = api_client.get_event_attendance(str(eventdate_id)) if eventdate_id else []

    return render_template(
        'views/admin/events_attendance.html',
        attendance_form=attendance_form,
        event_attendance=event_attendance,
    )


@main.route('/admin/_get_event')
def _get_event():
    event = [e for e in session['events'] if e['id'] == request.args.get('event')]
    if event:
        h = HTMLParser()
        event[0]['description'] = h.unescape(event[0]['description'])
        return jsonify(event[0])
    return ''


@main.route('/admin/_sync_paypal/<uuid:event_id>')
def _sync_paypal(event_id):
    api_client.sync_paypal(event_id)
    return ''


@main.route('/admin/_delete_event/<uuid:event_id>')
def _delete_event(event_id):
    api_client.delete_event(event_id)
    return redirect(url_for('main.admin_events'))


@main.route('/admin/_add_speaker')
def _add_speaker():
    name = request.args.get('name')
    if name:
        try:
            speaker = api_client.add_speaker(name)
            return jsonify(speaker)
        except HTTPError as e:
            return jsonify({'error': e.message})


@main.route('/admin/preview_event_detail')
def preview_event_detail():
    data = json.loads(urlparse.unquote(request.args.get('data')))

    current_app.logger.info(u'Preview args: {}'.format(data))

    venue = api_client.get_venue_by_id(data['venue_id'])

    data['fee'] = int(data['fee'])
    data['venue'] = venue
    data['formatted_event_datetimes'] = common_get_nice_event_dates(data['event_dates'])
    data['is_future_event'] = is_future_event(data)
    data['dates'] = api_client.get_event_dates(data['event_dates'])

    if venue['name'] == 'Online Event':
        data['event_type'] = 'Online ' + data['event_type']

    h = HTMLParser()
    data['_description'] = h.unescape(data['description'])

    return render_page(
        'views/event_details.html',
        event=data,
        preview="Events details: {}".format(data['title'])
    )


@main.route('/admin/preview_events')
def preview_events():
    data = json.loads(urlparse.unquote(request.args.get('data')))

    current_app.logger.info(u'Preview event banner args: {}'.format(data))

    data['formatted_event_datetimes'] = common_get_nice_event_dates(data['event_dates'])
    data['is_future_event'] = is_future_event(data)
    data['dates'] = api_client.get_event_dates(data['event_dates'])

    venue = api_client.get_venue_by_id(data['venue_id'])
    if venue['name'] == 'Online Event':
        data['event_type'] = 'Online ' + data['event_type']

    h = HTMLParser()
    data['_description'] = h.unescape(data['description'])

    return render_page(
        'views/events.html',
        future_events=[data],
        preview="Events page: {}".format(data['title'])
    )
