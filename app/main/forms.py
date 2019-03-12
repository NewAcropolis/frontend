from flask import session
from flask_wtf import FlaskForm
from wtforms import BooleanField, FormField, FieldList, FileField, HiddenField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired


class UserForm(FlaskForm):

    str_email = StringField()
    user_id = HiddenField()
    admin = BooleanField('admin')
    event = BooleanField('event')
    email = BooleanField('email')
    magazine = BooleanField('magazine')
    report = BooleanField('report')
    shop = BooleanField('shop')
    announcement = BooleanField('announcement')
    article = BooleanField('article')


class UserListForm(FlaskForm):
    users = FieldList(FormField(UserForm), min_entries=0)


def populate_user_form(users):
    user_list_form = UserListForm()

    if not user_list_form.users:
        for user in users:
            user_form = UserForm()
            user_form.user_id = user['id']
            user_form.str_email = user['email']

            user_form.admin = _has_access_area('admin', user['access_area'])
            user_form.event = _has_access_area('event', user['access_area'])
            user_form.email = _has_access_area('email', user['access_area'])
            user_form.magazine = _has_access_area('magazine', user['access_area'])
            user_form.report = _has_access_area('report', user['access_area'])
            user_form.shop = _has_access_area('shop', user['access_area'])
            user_form.announcement = _has_access_area('announcement', user['access_area'])
            user_form.article = _has_access_area('article', user['access_area'])

            user_list_form.users.append_entry(user_form)
    else:
        for user in user_list_form.users:
            found_user = [u for u in users if u['id'] == user.user_id.data]
            if found_user:
                user.str_email.data = found_user[0]['email']

    return user_list_form


def _has_access_area(area, user_access_area):
    if user_access_area:
        return area in user_access_area.split(',')
    return False


class EventForm(FlaskForm):

    events = SelectField('Events')
    event_type = SelectField('Event type', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    sub_title = StringField('Sub-title')
    description = TextAreaField('Description', validators=[DataRequired()])
    booking_code = StringField('Booking code')
    image_filename = FileField('Image filename')
    fee = StringField('Fee')
    conc_fee = StringField('Concession fee')
    multi_day_fee = StringField('Multi day fee')
    multi_day_conc_fee = StringField('Multi day concession fee')
    venue = SelectField('Venue')
    event_dates = HiddenField()
    start_time = HiddenField()
    end_time = HiddenField()
    speakers = SelectField('Speakers')
    dates_speakers = HiddenField()


def set_events(events, event_types, speakers, venues):
    form = EventForm()
    if form.events:
        if form.image_filename.data:
            filename = form.image_filename.data.filename
        else:
            filename = ''
        submitted_event = {
            'event_type': form.event_type.data,
            'title': form.title.data,
            'sub_title': form.sub_title.data,
            'description': form.description.data,
            'image_filename': filename,
            'fee': form.fee.data,
            'conc_fee': form.conc_fee.data,
            'multi_day_fee': form.multi_day_fee.data,
            'multi_day_conc_fee': form.multi_day_conc_fee.data,
            'venue': form.venue.data,
            'event_dates': form.event_dates.data,
            'start_time': form.start_time.data,
            'end_time': form.end_time.data,
            'dates_speakers': form.dates_speakers.data,
        }
        session['submitted_event'] = submitted_event

    form.events.choices = [('', 'New event')]

    for event in events:
        form.events.choices.append(
            (
                event['id'],
                '{} - {} - {}'.format(
                    event['event_dates'][0]['event_datetime'], event['event_type'], event['title'])
            )
        )

    form.event_type.choices = []

    for i, event_type in enumerate(event_types):
        form.event_type.choices.append(
            (event_type['event_type'], event_type['event_type'])
        )
        if event_type['event_type'] == 'Talk':
            form.event_type.default = (event_type['event_type'], event_type['event_type'])

    form.venue.choices = []

    default_venue = [v for v in venues if v['default']][0]
    form.venue.choices.append(
        (default_venue['id'], u'{} - {}'.format(default_venue['name'], default_venue['address']))
    )

    for venue in [v for v in venues if not v['default']]:
        form.venue.choices.append(
            (venue['id'], u'{} - {}'.format(venue['name'], venue['address']))
        )

    form.speakers.choices = [('', '')]
    for speaker in speakers:
        form.speakers.choices.append((speaker['id'], speaker['name']))

    return form