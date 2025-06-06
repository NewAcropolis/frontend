from datetime import datetime
from functools import cmp_to_key
from pytz import country_names
import re

from flask_wtf import FlaskForm, RecaptchaField
from wtforms import BooleanField, FormField, FieldList, FileField, HiddenField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, ValidationError

START_YEAR = 2021


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
    contact_recaptcha = RecaptchaField()

    def setup(self):
        self.contact_reasons.choices = [
            ('contact', 'Make contact'),
            ('bug', 'Report a problem on the website'),
            ('course', 'Ask about a course'),
            ('talk', 'Ask about a talk'),
            ('order', 'Order enquiry'),
            ('other', 'Other')
        ]


class ReservePlaceForm(FlaskForm):
    reserve_place_name = StringField('name', validators=[DataRequired()])
    reserve_place_email = StringField('email', validators=[DataRequired(), Email()])
    reserve_place_date_id = HiddenField()


class DeliveryForm(FlaskForm):
    first_name = StringField('first name', validators=[DataRequired()])
    last_name = StringField('last name', validators=[DataRequired()])
    address1 = StringField('address_1', validators=[DataRequired()])
    address2 = StringField('address_2')
    city = StringField('city')
    zip = StringField('post_code', validators=[DataRequired()])

    def set_delivery_address(self, address):
        self.first_name.data = address["first_name"]
        self.last_name.data = address["last_name"]
        self.address1.data = address["address1"]
        self.address2.data = address["address2"]
        self.city.data = address["city"]
        self.zip.data = address["zip"]


class EventAttendanceForm(FlaskForm):
    event_year = SelectField('event_year')
    events = SelectField('events')

    def setup_form(self, year, events, eventdate_id):
        self.event_year.choices = []
        for _year in range(datetime.now().year, START_YEAR, -1):
            self.event_year.choices.append((str(_year), str(_year)))
        self.event_year.choices.append((str(START_YEAR), str(START_YEAR)))

        if year:
            self.event_year.default = year
            self.process()

        self.events.choices = []

        if events:
            for event in events:
                for eventdate in event['event_dates']:
                    self.events.choices.append(
                        (
                            eventdate['id'],
                            u'{} - {} - {}'.format(
                                eventdate['event_datetime'], event['event_type'], event['title'])
                        )
                    )
            if eventdate_id:
                self.events.default = str(eventdate_id)
                self.process()
        else:
            self.events.choices.append(('', 'No events found'))

    def set_eventdate_id(self, eventdate_id):
        self.events.default = str(eventdate_id)
        self.process()


class MagazineForm(FlaskForm):
    title = StringField('title', validators=[DataRequired()])
    magazines = SelectField('Magazines')
    magazine_filename = FileField('Magazine filename')
    next_issue = HiddenField('Next issue no')
    existing_magazine_filename = HiddenField('Existing magazine filename')
    topics = TextAreaField('Topics')
    tags = HiddenField()
    old_tags = HiddenField()

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


class ArticleForm(FlaskForm):
    title = StringField('title', validators=[DataRequired()])
    author = StringField('author', validators=[DataRequired()])
    articles = SelectField('Articles')
    magazines = SelectField('Magazines')
    image_filename = FileField('Image filename')
    existing_image_filename = HiddenField('Existing image filename')
    reject_reason = TextAreaField('Reject reason')
    article_content = TextAreaField('Content')
    article_state = HiddenField()
    tags = HiddenField()
    old_tags = HiddenField()

    def set_article_form(self, articles, magazines, tags):
        self.magazines.choices = [('', 'No magazine link')]
        for magazine in magazines:
            self.magazines.choices.append(
                (
                    magazine['id'],
                    magazine['title']
                )
            )

        self.articles.choices = [('', '== New article ==')]

        articles_list = []

        for article in articles:
            tagged = False
            if tags:
                for tag in tags.lower().split(','):
                    if article.get('tags') and tag + ',' in article.get('tags').lower() + ',':
                        tagged = True
            articles_list.append(
                (
                    article['id'],
                    ("* " if tagged else "") + article['title']
                )
            )

        def article_compare(a, b):
            if a[1].startswith('*'):
                if b[1].startswith('*'):
                    if a[1] < b[1]:
                        return -1
                    else:
                        return 1
                else:
                    return -1
            else:
                if a[1] < b[1]:
                    return -1
                else:
                    return 1

        article_compare_key = cmp_to_key(article_compare)
        articles_list.sort(key=article_compare_key)
        self.articles.choices = articles_list


class SelectedTagsForm(FlaskForm):
    selected_tags = HiddenField()
    active = HiddenField(default=0)

    def set_selected_tags_form(self, tags):
        self.selected_tags.data = tags


class ArticlesZipfileForm(FlaskForm):
    articles_zipfile = FileField('Zip file of articles')
    magazines = SelectField('Magazines')

    def set_articles_zipfile_form(self, magazines):
        self.magazines.choices = [('', 'No magazine link')]
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
    order = BooleanField('order')
    magazine = BooleanField('magazine')
    cache = BooleanField('cache')
    announcement = BooleanField('announcement')
    article = BooleanField('article')
    member = BooleanField('member')


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
                user_form.order = _has_access_area('order', user['access_area'])
                user_form.magazine = _has_access_area('magazine', user['access_area'])
                user_form.report = _has_access_area('report', user['access_area'])
                user_form.cache = _has_access_area('cache', user['access_area'])
                user_form.announcement = _has_access_area('announcement', user['access_area'])
                user_form.article = _has_access_area('article', user['access_area'])
                user_form.member = _has_access_area('member', user['access_area'])

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
    description = TextAreaField('Description')
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
    remote_access = StringField('Remote access')
    remote_pw = StringField('Remote password')
    show_banner_text = BooleanField('Show banner text?', default=True)
    headline = BooleanField('Headline?', default=False)

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

    def is_pending(self, event):
        return 'pending' in event.keys()

    def is_deleting(self, event):
        return event.get('pending') == 'delete'

    def set_events(self, form_select, events, first_item_text=''):
        form_select.choices = [('', first_item_text)]
        pending_events = []

        for event in events:
            is_pending = self.is_pending(event)
            is_deleting = self.is_deleting(event)
            prefix = ''
            if is_pending:
                pending_events.append(event['id'])
                prefix = f'[pending {event["pending"]}] '
            elif event['id'] in pending_events:
                continue

            _eventdate = event['event_dates'][0]['event_datetime'] if not is_pending or is_deleting \
                else event['event_dates'][0]['event_date']

            form_select.choices.append(
                (
                    event['id'],
                    u'{} - {} - {}'.format(
                        _eventdate, prefix + event['event_type'], event['title'])
                )
            )


class EmailForm(FlaskForm):

    emails = SelectField('Emails')
    email_types = SelectField('Email Types')
    events = SelectField('Events')
    details = TextAreaField('Details')
    extra_txt = TextAreaField('Extra text')
    subject = StringField('Subject')
    basic_content = TextAreaField('Basic Content')
    submit_type = HiddenField()
    send_starts_at = HiddenField()
    email_state = HiddenField()
    expires = HiddenField()
    events_emailed = HiddenField()
    reject_reason = TextAreaField('Reject reason')

    def set_emails_form(self, emails, email_types, events):
        pending_emails = []
        self.emails.choices = [('', 'New email')]
        email_events = []
        for email in emails:
            is_pending = 'pending' in email.keys()
            prefix = ''
            if is_pending:
                pending_emails.append(email['id'])
                prefix = f'[pending {email["pending"]}] '
            elif email['id'] in pending_emails:
                continue

            if email['email_type'] == 'event' and email.get('event_id'):
                email_events.append(email['event_id'])

            self.emails.choices.append(
                (
                    email['id'],
                    prefix + email['subject'] if 'subject' in email else email['title']
                )
            )

        if email_events:
            self.events_emailed.data = ','.join(email_events)

        self.email_types.choices = []
        for email_type in email_types:
            self.email_types.choices.append(
                (
                    email_type['type'],
                    email_type['type']
                )
            )

        # Set event choice first option to show events
        # TODO: this probably needs fixing
        self.events.choices = [('No event', 'No event')]
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


#  regex from https://en.wikipedia.org/wiki/Postcodes_in_the_United_Kingdom
postcode_re = re.compile(r'^[A-Z]{1,2}[0-9R][0-9A-Z]?\s?[0-9][A-Z]{2}$')


def check_postcode(form, field):
    if not postcode_re.match(field.data):
        raise ValidationError('{} not valid postcode'.format(field.data))


class MissingAddressForm(FlaskForm):
    street = StringField('House number and street', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    state = StringField('State')
    postcode = StringField('Postcode', validators=[DataRequired(), check_postcode])
    country = SelectField('Country')

    def setup_country(self, do_process):
        _country_names = dict(country_names)
        _country_names['GB'] = "United Kingdom"
        self.country.choices = [
            (c, _country_names[c]) for c in sorted(_country_names, key=_country_names.get)
        ]
        self.country.default = 'GB'

        if do_process:
            self.process()


class UnsubscribeForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    recaptcha = RecaptchaField()


class UpdateMemberForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    verify_email = StringField('Verify Email', validators=[DataRequired()])
    recaptcha = RecaptchaField()


class QueueForm(FlaskForm):
    status_filter = SelectField('status_filter')

    def setup_status_filter(self):
        self.status_filter.choices = [("new", "new"), ("ok", "ok"), ("error", "error"), ("suspend", "suspend")]


class OrderForm(FlaskForm):
    created_at = StringField()
    transaction_id = StringField()
    txn_id = StringField()
    buyer_name = StringField()
    payment_total = StringField()
    delivery_status = StringField()
    delivery_sent = BooleanField()
    refund_issued = BooleanField()
    notes = TextAreaField()
    books = []
    tickets = []

    def populate_order_form(self, order):
        self.created_at = order['created_at']
        self.transaction_id = order['txn_id']
        self.txn_id = order['txn_id']
        self.buyer_name = order['buyer_name']
        self.payment_total = order['payment_total']
        self.delivery_status = order['delivery_status'] if order['delivery_status'] else 'Not applicable'
        self.delivery_sent.data = order['delivery_sent'] is True
        self.refund_issued.data = order['refund_issued'] is True
        self.notes.data = order['notes']


class OrderListForm(FlaskForm):
    order_year = SelectField('order_year')

    orders = FieldList(FormField(OrderForm), min_entries=0)

    def setup_order_year(self, year=None):
        self.order_year.choices = []
        for _year in range(datetime.now().year, START_YEAR, -1):
            self.order_year.choices.append((_year, _year))
        self.order_year.choices.append((START_YEAR, START_YEAR))

        if year:
            self.order_year.default = year
            self.process()

    def populate_order_list_form(self, orders):
        if not self.orders:
            for order in orders:
                order_form = OrderForm()
                order_form.created_at = order['created_at']
                order_form.transaction_id = order['txn_id']
                order_form.txn_id = order['txn_id']
                order_form.buyer_name = order['buyer_name']
                order_form.payment_total = order['payment_total']
                order_form.delivery_status = order['delivery_status'] if order['delivery_status'] else 'Not applicable'
                order_form.delivery_sent = order['delivery_sent'] == 'True'
                order_form.refund_issued = order['refund_issued'] == 'True'
                order_form.notes.data = order['notes']
                # order_form.books = order.books

                self.orders.append_entry(order_form)


class MemberForm(FlaskForm):
    email_address = StringField('Email address')
    name = StringField("Name")
    active = BooleanField()
    unsubcode = HiddenField()
