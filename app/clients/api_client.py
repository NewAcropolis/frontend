from datetime import datetime
from flask import current_app
from functools import wraps

from app.cache import Cache
from app.clients import BaseAPIClient
from na_common.dates import get_nice_event_dates as common_get_nice_event_dates


def only_show_approved_events(func):
    @wraps(func)
    def _only_show_approved_events(*args, **kwargs):
        events = func(*args)
        if kwargs.get('approved_only'):
            return [e for e in events if e.get('event_state') == 'approved']
        return events
    return _only_show_approved_events


def get_events_intro_courses_prioritised(events):
    intro_courses_first = []
    other_events = []
    for event in events:
        if event['event_type'] == 'Introductory Course':
            intro_courses_first.append(event)
        else:
            other_events.append(event)

    intro_courses_first.extend(other_events)
    return intro_courses_first


def use_cache(**dkwargs):
    def use_cache_inner(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'from_cache' in dkwargs:
                for cache_name in dkwargs['from_cache'].split(','):
                    data_cache = Cache.get_data(cache_name)
                    if len(args) == 2:
                        data = [d for d in data_cache if d[dkwargs['key']] == str(args[1])]
                        if len(data) > 0:
                            data = data[0]
                            break
                    else:
                        current_app.logger.info("from_cache not 2 args")
            else:
                data = Cache.get_data(f.func_name)

                if data and dkwargs.get('update_daily'):
                    updated_on = Cache.get_updated_on(f.func_name)
                    kwargs['func'] = f
                    if 'decorator' in dkwargs:
                        kwargs['decorator'] = dkwargs['decorator']
                    if 'sort_by' in dkwargs:
                        kwargs['sort_by'] = dkwargs['sort_by']
                    if (datetime.utcnow() - updated_on).seconds > 60*60*24:  # update pages once a day
                        update_cache(*args, **kwargs)

            if not data:
                if 'db_call' in dkwargs:
                    data = dkwargs['db_call'](*args, **kwargs)
                else:
                    data = f(*args, **kwargs)
                if 'from_cache' not in dkwargs:
                    Cache.set_data(f.func_name, data)
            return data
        return decorated
    return use_cache_inner


def update_cache(*args, **kwargs):
    func = kwargs.pop('func')
    cache_func_name = func.func_name.replace("_from_db", "")
    cached_data = Cache.get_data(cache_func_name)
    if 'decorator' in kwargs:
        func = kwargs['decorator'](func)

    data = func(*args, **kwargs)

    review_data = Cache.get_review_entities(func.func_name)

    if review_data and 'sort_by' in kwargs:
        sort_by = kwargs.pop('sort_by')
        data = sort_by(data.extend(review_data))

    if cached_data != data:
        current_app.logger.info('Cache updated from db')
        Cache.set_data(cache_func_name, data)
    else:
        current_app.logger.info('Cache does not need updating for {}'.format(func.func_name))

    Cache.purge_older_versions(func.func_name)


class ApiClient(BaseAPIClient):
    def init_app(self, app):
        super(ApiClient, self).init_app(app)

    def get_speakers(self):
        return self.get(url='speakers')

    def add_speaker(self, name):
        data = {'name': name}

        return self.post(url='speaker', data=data)

    def get_venues(self):
        return self.get(url='venues')

    def get_venue_by_id(self, venue_id):
        return self.get(url='venue/{}'.format(venue_id))

    def add_event(self, event):
        return self.post(url='event', data=event)

    def delete_event(self, event_id):
        return self.delete(url='event/{}'.format(event_id))

    def update_event(self, event_id, event):
        return self.post(url='event/{}'.format(event_id), data=event)

    def get_event_by_id_from_db(self, event_id):
        return self.get_nice_event_date(self.get(url='event/{}'.format(event_id)))

    @use_cache(
        db_call=get_event_by_id_from_db,
        from_cache='get_events_in_future,get_events_past_year',
        key='id')
    def get_event_by_id(self, event_id):
        return self.get_event_by_id_from_db(event_id)

    def get_event_by_old_id(self, event_id):
        event = self.get(url='legacy/event_handler?eventid={}'.format(event_id))
        if event:
            return self.get_nice_event_date(event)

    def get_event_types(self):
        return self.get(url='event_types')

    def get_limited_events(self):
        return self.get_nice_event_dates(self.get(url='events/limit/30'))

    def get_latest_magazine_from_db(self):
        return self.get(url='magazine/latest')

    @use_cache(db_call=get_latest_magazine_from_db)
    def get_latest_magazine(self):
        return self.get(url='magazine/latest')

    @only_show_approved_events
    def get_events_in_future_from_db(self):
        events = self.get_nice_event_dates(self.get(url='events/future'), future_dates_only=True)
        return get_events_intro_courses_prioritised(events)

    @use_cache(
        update_daily=True,
        decorator=only_show_approved_events,
        approved_only=True,  # used by only_show_approved_events
        db_call=get_events_in_future_from_db,
        sort_by=get_events_intro_courses_prioritised)
    @only_show_approved_events
    def get_events_in_future(self):
        return self.get_events_in_future_from_db()

    @only_show_approved_events
    def get_events_past_year_from_db(self):
        return self.get_nice_event_dates(self.get(url='events/past_year'))

    @use_cache(update_daily=True, db_call=get_events_past_year_from_db)
    def get_events_past_year(self):
        return self.get_events_past_year_from_db()

    def add_email(self, email):
        return self.post(url='email', data=email)

    def update_email(self, email_id, email):
        return self.post(url='email/{}'.format(email_id), data=email)

    def get_email_types(self):
        return self.get(url='email/types')

    def post_email_preview(self, data):
        return self.post(url='email/preview', data=data)

    def get_future_emails(self):
        return self.get(url='emails/future')

    def get_info(self):
        return self.get(url='')

    def get_latest_emails(self):
        return self.get(url='emails/latest')

    def get_articles_summary_from_db(self):
        return self.get(url='articles/summary')

    @use_cache(update_daily=True, db_call=get_articles_summary_from_db)
    def get_articles_summary(self):
        return self.get_articles_summary_from_db()

    def get_article(self, id):
        return self.get(url='article/{}'.format(id))

    def add_magazine(self, magazine):
        return self.post(url='magazine', data=magazine)

    def update_magazine(self, id, magazine):
        return self.post(url='magazine/{}'.format(id), data=magazine)

    def get_magazine(self, id):
        return self.get(url='magazine/{}'.format(id))

    def get_magazines(self):
        return self.get(url='magazines')

    def get_member_from_unsubcode(self, unsubcode):
        return self.get(url='member/{}'.format(unsubcode))

    def unsubscribe_member(self, unsubcode):
        return self.post(url='member/unsubscribe/{}'.format(unsubcode), data=None)

    def update_member(self, unsubcode, name, email):
        data = {
            'name': name,
            'email': email
        }
        return self.post(url='member/update/{}'.format(unsubcode), data=data)

    def get_marketings(self):
        return self.get(url='marketings')

    def get_nice_event_dates(self, events, future_dates_only=False):
        for event in events:
            if future_dates_only:
                event['event_dates'] = self.get_future_event_dates(event['event_dates'])

            event = self.get_nice_event_date(event)
        return events

    def get_nice_event_date(self, event):
        event['formatted_event_datetimes'] = common_get_nice_event_dates(event['event_dates'])
        event['dates'] = self.get_event_dates(event['event_dates'])

        event_date = event["event_dates"][0]
        _datetime = datetime.strptime(event_date["event_datetime"], '%Y-%m-%d %H:%M')
        if event['event_type'] == 'Introductory Course':
            event['event_monthyear'] = _datetime.strftime('%B %Y')

        event_date['event_time'] = _datetime.strftime('%H:%M')
        if not event.get('event_time'):
            event['event_time'] = event_date['event_time']
        else:
            if _datetime.minute > 0:
                time = _datetime.strftime('%-I:%M %p')
            else:
                time = _datetime.strftime('%-I %p')
            event['event_time'] = time
        if not event.get('end_time'):
            event['end_time'] = event_date["end_time"]

        return event

    def get_future_event_dates(self, event_dates):
        future_dates = []
        for event_date in event_dates:
            _datetime = datetime.strptime(event_date["event_datetime"], '%Y-%m-%d %H:%M')
            if _datetime >= datetime.today():
                future_dates.append(event_date)

        return future_dates

    def get_event_dates(self, event_dates):
        dates = []
        for event_date in event_dates:
            _datetime = datetime.strptime(event_date["event_datetime"], '%Y-%m-%d %H:%M')
            dates.append(_datetime.strftime('%Y-%m-%d'))

        return dates

    def get_user(self, email):
        return self.get(url='user/{}'.format(email))

    def get_users(self):
        return self.get(url='users')

    def create_user(self, profile):
        data = {
            'email': profile['email'],
            'name': profile['name'],
        }
        return self.post(url='user', data=data)

    def update_user_access_area(self, user_id, access_area):
        data = {
            'access_area': access_area
        }
        return self.post(url='user/{}'.format(user_id), data=data)

    def add_subscription_email(self, name, email, marketing_id):
        data = {
            'name': name,
            'email': email,
            'marketing_id': marketing_id
        }
        return self.post(url='member/subscribe', data=data)

    def send_message(self, name, email, reason, message):
        data = {
            'name': name,
            'email': email,
            'reason': reason,
            'message': message,
        }

        return self.post(url='send_message', data=data)
