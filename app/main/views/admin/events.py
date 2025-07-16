import base64
from flask import current_app, jsonify, redirect, render_template, request, session, url_for
from html import unescape, escape
import json
import urllib.parse as urlparse

from app import api_client
from app.clients.errors import HTTPError
from app.clients.utils import get_event_dates, size_from_b64
from app.main import main
from app.main.forms import EventAttendanceForm, EventForm
from app.main.views import render_page
from app.main.views.events import is_future_event
from app.clients.utils import get_nice_event_date, upload_blob_from_base64string
from app.queue import Queue
from app.cache import Cache

from na_common.dates import get_nice_event_dates as common_get_nice_event_dates

EVENT_STATES = ['new', 'draft', 'ready', 'approved', 'rejected']


def is_admin_user():
    user = session['user']
    return 'admin' in user.get('access_area') or user.get('access_area') == 'admin'


def get_value(json_obj, id, return_value):
    for p in json_obj:
        if p['id'] == id:
            return p[return_value]


@main.route('/admin/events', methods=['GET', 'POST'])
@main.route('/admin/events/<string:selected_event_id>', methods=['GET', 'POST'])
@main.route('/admin/events/<string:selected_event_id>/<api_message>', methods=['GET', 'POST'])
def admin_events(selected_event_id=None, api_message=None):
    events = api_client.get_pending_and_limited_events()
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
            'id': form.events.data,
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
            'event_state': form.submit_type.data if form.submit_type.data in EVENT_STATES else 'new',
            'reject_reasons': reject_reasons,
            'remote_access': form.remote_access.data,
            'remote_pw': form.remote_pw.data,
            'show_banner_text': form.show_banner_text.data,
            'headline': form.headline.data
        }

        adjusted_event = event.copy()

        adjusted_event['description'] = escape(event['description'])
        adjusted_event['event_dates'] = json.loads(str(event['event_dates']))
        file_request = request.files.get('image_filename')
        if file_request:
            file_data = file_request.read()
            file_data_encoded = base64.b64encode(file_data)
            _file_size = size_from_b64(str(file_data_encoded))
            if _file_size > current_app.config['MAX_IMAGE_SIZE']:
                _file_size_mb = round(_file_size/(1024*1024), 1)
                _max_size_mb = current_app.config['MAX_IMAGE_SIZE']/(1024*1024)
                errors.append("Image {} file size ({} mb) is larger than max ({} mb)".format(
                    file_request.filename, _file_size_mb, _max_size_mb))
            else:
                tmp_filename = f"tmp/{filename}"
                upload_blob_from_base64string(filename, tmp_filename, file_data_encoded)
                adjusted_event['image_filename'] = tmp_filename

        if not errors:
            # remove empty values
            for key, value in event.items():
                if value != 0 and not value:
                    del adjusted_event[key]

            try:
                message = None

                for d in adjusted_event['event_dates']:
                    d['event_datetime'] = d['event_date']

                adjusted_event['event_type'] = get_value(event_types, adjusted_event['event_type_id'], 'event_type')
                adjusted_event = get_nice_event_date(adjusted_event)
                adjusted_event['venue'] = {}
                adjusted_event['venue']['id'] = adjusted_event['venue_id']

                if event.get('event_id'):
                    response = api_client.update_event(event['event_id'], adjusted_event)
                    message = 'event updated'
                else:
                    session['events'] = events.append(adjusted_event)
                    response = api_client.add_event(adjusted_event)

                if 'error' in session:
                    raise HTTPError(response, message=session.pop('error'))

                return redirect(url_for('main.admin_events', selected_event_id=response.get('id'), api_message=message))
            except HTTPError as e:
                current_app.logger.error(e)
                temp_event = json.dumps(event)
                if "message" in e.message:
                    errors = [escape(e.message['message'])]
                else:
                    errors = json.dumps(escape(e.message))
    elif form.errors:
        errors = [escape(str(form.errors))]
        selected_event_id = form.events.data

    return render_template(
        'views/admin/events.html',
        form=form,
        images_url=current_app.config['IMAGES_URL'],
        selected_event_id=selected_event_id,
        message=api_message,
        temp_event=temp_event,
        errors=json.dumps(errors) if errors else None,
        limited_events_last_updated=Cache.get_updated_on('get_limited_events').strftime('%d/%m/%Y %H:%M')
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
        event[0] = get_nice_event_date(event[0], set_timemarkers=False)
        if 'image_data' in event[0].keys():
            event[0]['image_data'] = base64.b64decode(event[0]['image_data']).decode('utf-8')
        if event[0].get('pending'):
            q_item = Queue.get_item_by_payload_key('pending_events', 'id', event[0]['id'])
            event[0]['held_until'] = Queue.hold_off_processing(q_item).strftime('%-I:%M %p')
        if 'description' in event[0].keys():
            event[0]['description'] = unescape(event[0]['description'])
        else:
            event[0]['description'] = ''
        return jsonify(event[0])
    return ''


@main.route('/admin/_sync_paypal/<uuid:event_id>')
def _sync_paypal(event_id):
    api_client.sync_paypal(event_id)
    return ''


@main.route('/admin/_delete_event/<string:event_id>')
def _delete_event(event_id):
    api_client.delete_event(event_id)
    return redirect(url_for('main.admin_events', selected_event_id=event_id))


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
    data['formatted_event_datetimes'] = common_get_nice_event_dates(data['event_dates'],
                                                                    data['event_type'] != 'Competition')
    data['is_future_event'] = is_future_event(data)
    data['dates'] = get_event_dates(data['event_dates'])

    if venue['name'] == 'Online Event':
        data['event_type'] = 'Online ' + data['event_type']

    data['_description'] = unescape(data['description'])

    return render_page(
        'views/event_details.html',
        event=data,
        preview="Events details: {}".format(data['title'])
    )


@main.route('/admin/preview_events')
def preview_events():
    data = json.loads(urlparse.unquote(request.args.get('data')))

    current_app.logger.info(u'Preview event banner args: {}'.format(data))

    data['formatted_event_datetimes'] = common_get_nice_event_dates(data['event_dates'],
                                                                    data['event_type'] != 'Competition')
    data['is_future_event'] = is_future_event(data)
    data['dates'] = get_event_dates(data['event_dates'])

    venue = api_client.get_venue_by_id(data['venue_id'])
    if venue['name'] == 'Online Event':
        data['event_type'] = 'Online ' + data['event_type']

    data['_description'] = unescape(data['description'])

    return render_page(
        'views/events.html',
        future_events=[data],
        preview="Events page: {}".format(data['title'])
    )
