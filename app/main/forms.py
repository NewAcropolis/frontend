import re

from flask_wtf import FlaskForm, RecaptchaField
from wtforms import BooleanField, FormField, FieldList, FileField, HiddenField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, ValidationError


class SlimSubscriptionForm(FlaskForm):
    slim_subscription_email = StringField('email', validators=[DataRequired(), Email()])

class SubscriptionForm(FlaskForm):
    subscription_name = StringField('name')
    subscription_email = StringField('email', validators=[DataRequired(), Email()])
    subscription_marketings = SelectField('marketings')

    def setup(self, marketings):
        self.subscription_marketings.choices = [
            (m['id'], m['description']) for m in marketings
        ]
        self.subscription_marketings.choices.insert(0, ('', 'How did you hear about us?'))
        self.subscription_marketings.default = ''

    def validate_subscription_marketings(form, field):
        if not field.data:
            raise ValidationError("Please select a marketing option")


class ContactForm(FlaskForm):
    contact_name = StringField('name', validators=[DataRequired()])
    contact_email = StringField('email', validators=[DataRequired(), Email()])
    contact_message = TextAreaField('message', validators=[DataRequired()])
    contact_reasons = SelectField('reasons', validators=[DataRequired()])

    def setup(self):
        self.contact_reasons.choices = [
            ('contact', 'Make contact'),
            ('bug', 'Report a problem on the website'),
            ('course', 'Ask about a course'),
            ('talk', 'Ask about a talk'),
            ('other', 'Other')
        ]


class MagazineForm(FlaskForm):
    title = StringField('title', validators=[DataRequired()])
    magazines = SelectField('Magazines')
    magazine_filename = FileField('Magazine filename')
    next_issue = HiddenField('Next issue no')
    existing_magazine_filename = HiddenField('Existing magazine filename')
    topics = TextAreaField('Topics')

    def set_magazine_form(self, magazines):
        MAGAZINE_PATTERN = r'Issue (?P<issue_no>\d+)'
        match = re.search(MAGAZINE_PATTERN, magazines[0]['title'])
        if match:
            issue_no = match.group('issue_no')
            self.next_issue.data = "Issue %s" % (int(issue_no) + 1)

        self.magazines.choices = [('', 'New magazine')]

        for magazine in magazines:
            self.magazines.choices.append(
                (
                    magazine['id'],
                    magazine['title']
                )
            )


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


class EmailForm(FlaskForm):

    emails = SelectField('Emails')
    email_types = SelectField('Email Types')
    events = SelectField('Events')
    details = TextAreaField('Details')
    extra_txt = TextAreaField('Extra text')
    submit_type = HiddenField()
    send_starts_at = HiddenField()
    email_state = HiddenField()
    expires = HiddenField()
    events_emailed = HiddenField()
    reject_reason = TextAreaField('Reject reason')

    def set_emails_form(self, emails, email_types, events):
        self.emails.choices = [('', 'New email')]
        email_events = []
        for email in emails:
            if email['email_type'] == 'event':
                email_events.append(email['event_id'])

            self.emails.choices.append(
                (
                    email['id'],
                    email['subject']
                )
            )

        self.events_emailed.data = ','.join(email_events)

        self.email_types.choices = []
        for email_type in email_types:
            self.email_types.choices.append(
                (
                    email_type['type'],
                    email_type['type']
                )
            )

        self.events.choices = []
        if events:
            for event in events:
                event_dates = [e['event_datetime'][5:-6] for e in event['event_dates']]
                parts = [
                    "{}/{}".format(date_parts[1].lstrip('0'), date_parts[0].lstrip('0'))
                    for date_parts in [date.split('-') for date in event_dates]
                ]
                self.events.choices.append(
                    (
                        event['id'],
                        u'{} - {} - {}'.format(
                            ", ".join(parts),
                            event['event_type'],
                            event['title']
                        )
                    )
                )
        else:
            self.events.choices.append(('', ''))


class UnsubscribeForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    recaptcha = RecaptchaField()


class UpdateMemberForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    verify_email = StringField('Verify Email', validators=[DataRequired()])
    recaptcha = RecaptchaField()
