from flask_wtf import FlaskForm
from wtforms import BooleanField, FormField, FieldList, FileField, HiddenField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email


class SubscriptionForm(FlaskForm):
    email = StringField('email', validators=[DataRequired(), Email()])


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

    def populate_user_form(self, users):
        if not self.users:
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

                self.users.append_entry(user_form)
        else:
            for user in self.users:
                found_user = [u for u in users if u['id'] == user.user_id.data]
                if found_user:
                    user.str_email.data = found_user[0]['email']


def _has_access_area(area, user_access_area):
    if user_access_area:
        return area in user_access_area.split(',')
    return False


class EventForm(FlaskForm):

    events = SelectField('Events')
    alt_event_images = SelectField('Event Images')
    event_type = SelectField('Event type', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    sub_title = StringField('Sub-title')
    description = TextAreaField('Description', validators=[DataRequired()])
    booking_code = StringField('Booking code')
    image_filename = FileField('Image filename')
    existing_image_filename = HiddenField('Existing image filename')
    fee = StringField('Fee')
    conc_fee = StringField('Concession fee')
    multi_day_fee = StringField('Multi day fee')
    multi_day_conc_fee = StringField('Multi day concession fee')
    venue = SelectField('Venue')
    event_dates = HiddenField()
    start_time = HiddenField()
    end_time = HiddenField()
    speakers = SelectField('Speakers')
    dates = HiddenField()
    default_event_type = HiddenField()
    submit_type = HiddenField()
    reject_reason = TextAreaField('Reject reason')
    reject_reasons_json = HiddenField()

    def set_events_form(self, events, event_types, speakers, venues):
        self.set_events(self.events, events, 'New event')
        self.set_events(self.alt_event_images, events, 'Or use an existing event image:')

        self.event_type.choices = []

        for i, event_type in enumerate(event_types):
            if event_type['event_type'] == 'Talk':
                self.default_event_type.data = i

            self.event_type.choices.append(
                (event_type['id'], event_type['event_type'])
            )

        self.venue.choices = []

        default_venue = [v for v in venues if v['default']][0]
        self.venue.choices.append(
            (default_venue['id'], u'{} - {}'.format(default_venue['name'], default_venue['address']))
        )

        for venue in [v for v in venues if not v['default']]:
            self.venue.choices.append(
                (venue['id'], u'{} - {}'.format(venue['name'], venue['address']))
            )

        self.speakers.choices = [('', ''), ('new', 'Create new speaker')]
        for speaker in speakers:
            self.speakers.choices.append((speaker['id'], speaker['name']))

    def set_events(self, form_select, events, first_item_text=''):
        form_select.choices = [('', first_item_text)]

        for event in events:
            form_select.choices.append(
                (
                    event['id'],
                    u'{} - {} - {}'.format(
                        event['event_dates'][0]['event_datetime'], event['event_type'], event['title'])
                )
            )
