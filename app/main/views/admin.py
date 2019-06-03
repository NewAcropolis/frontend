import base64
from flask import current_app, jsonify, redirect, render_template, request, session, url_for
import json
import urlparse
# from werkzeug import secure_filename

from requests_oauthlib import OAuth2Session

from app import api_client
from app.clients.errors import HTTPError
from app.main import main
from app.main.forms import UserListForm, EventForm
from app.main.views import requires_google_auth


def is_admin_user():
    user = session['user']
    return 'admin' in user.get('access_area') or user.get('access_area') == 'admin'


@main.route('/admin')
def admin():
    return render_template(
        'views/admin/admin.html',
        name=session['user_profile']['name']
    )


@main.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    users = [u for u in api_client.get_users() if u.get('access_area') != 'admin']
    form = UserListForm()
    update_count = 0

    if form.validate_on_submit():
        for i, user in enumerate(form.users):
            access_area = ''
            if user.admin.data:
                access_area += 'admin,'
            if user.event.data:
                access_area += 'event,'
            if user.email.data:
                access_area += 'email,'
            if user.magazine.data:
                access_area += 'magazine,'
            if user.report.data:
                access_area += 'report,'
            if user.shop.data:
                access_area += 'shop,'
            if user.announcement.data:
                access_area += 'announcement,'
            if user.article.data:
                access_area += 'article,'

            if users[i]['access_area'] != access_area:
                update_count += 1
                api_client.update_user_access_area(users[i]['id'], access_area)

    form.populate_user_form(users)

    return render_template(
        'views/admin/users.html',
        users=users,
        update_count=update_count,
        access_areas=current_app.config['ACCESS_AREAS'],
        form=form
    )


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
            'reject_reasons': reject_reasons
        }

        adjusted_event = event.copy()

        from cgi import escape
        adjusted_event['description'] = escape(event['description'])
        adjusted_event['event_dates'] = json.loads(str(event['event_dates']))

        file_request = request.files.get('image_filename')
        if file_request:
            # filename = secure_filename(file_request.filename)
            file_data = file_request.read()
            file_data_encoded = base64.b64encode(file_data)

            adjusted_event['image_data'] = file_data_encoded

        # remove empty values
        for key, value in event.iteritems():
            if not value:
                del adjusted_event[key]

        try:
            message = None
            if event.get('event_id'):
                response = api_client.update_event(event['event_id'], adjusted_event)
                message = 'event updated'
            else:
                response = api_client.add_event(adjusted_event)

            return redirect(url_for('main.admin_events', selected_event_id=response['id'], api_message=message))
        except HTTPError as e:
            current_app.logger.error(e)
            temp_event = json.dumps(event)
            errors = json.dumps(e.message)

    return render_template(
        'views/admin/events.html',
        form=form,
        images_url=current_app.config['IMAGES_URL'],
        selected_event_id=selected_event_id,
        message=api_message,
        is_admin_user=is_admin_user(),
        temp_event=temp_event,
        errors=errors
    )


@main.route('/admin/_get_event')
def _get_event():
    event = [e for e in session['events'] if e['id'] == request.args.get('event')]
    if event:
        from HTMLParser import HTMLParser
        h = HTMLParser()
        event[0]['description'] = h.unescape(event[0]['description'])
        return jsonify(event[0])
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


@main.route('/admin/preview_event')
def preview_event():
    data = json.loads(urlparse.unquote(request.args.get('data')))

    current_app.logger.info(u'Preview args: {}'.format(data))

    venue = api_client.get_venue_by_id(data['venue_id'])

    data['venue'] = venue

    return render_template(
        'views/admin/preview.html',
        images_url=current_app.config['IMAGES_URL'],
        events=[data],
        api_base_url=api_client.base_url,
        paypal_account=current_app.config['PAYPAL_ACCOUNT']
    )


@main.route("/profile", methods=["GET"])
@requires_google_auth
def profile():
    """Fetching a protected resource using an OAuth 2 token.
    """

    google = OAuth2Session(current_app.config['GOOGLE_OAUTH2_CLIENT_ID'], token=session['oauth_token'])
    return jsonify(google.get('https://www.googleapis.com/oauth2/v1/userinfo').json())
