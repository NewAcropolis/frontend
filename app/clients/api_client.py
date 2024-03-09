from datetime import datetime
from flask import current_app, request, session
from functools import wraps
import hashlib
import json
import os

from app.config import use_sim_data
from app.cache import Cache
from app.queue import Queue
from app.clients import BaseAPIClient
from app.clients.utils import get_nice_event_dates, get_nice_event_date


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


def call_sim_function(f, *args, **kwargs):
    import importlib
    mod = importlib.import_module('app.clients.sim_data')
    func = getattr(mod, 'sim_' + f.__name__)
    return func(*args, **kwargs)


def sim_data_available(**dkwargs):
    def sim_data_available_inner(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if os.environ.get('ENVIRONMENT', 'development') != 'live' and request.args.get('test') == 'sim_data':
                return call_sim_function(f, args, kwargs)
            return f(*args, **kwargs)
        return decorated
    return sim_data_available_inner


def use_cache(**dkwargs):
    def use_cache_inner(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'test' in request.args and request.args.get('test') != 'sim_data':
                if f.__name__ == 'get_event_by_id':
                    from app.clients.test_data import get_intro_course
                    if request.args.get('test') == 'intro':
                        return get_intro_course()
                    elif request.args.get('test') == 'intro_external':
                        return get_intro_course(external=True)
            elif use_sim_data():
                return call_sim_function(f, args, kwargs)
            elif current_app.config['TESTING']:
                if 'db_call' in dkwargs:
                    data = dkwargs['db_call'](*args, **kwargs)
                else:
                    data = f(*args, **kwargs)
                return data

            data = None
            if 'from_cache' in dkwargs:
                for cache_name in dkwargs['from_cache'].split(','):
                    data_cache = Cache.get_data(cache_name)
                    if data_cache is not None:
                        if len(args) == 2:
                            data = [d for d in data_cache if d[dkwargs['key']] == str(args[1])]
                            if len(data) > 0:
                                data = data[0]
                                break
                        else:
                            current_app.logger.info("from_cache not 2 args")
            else:
                data = Cache.get_data(f.__name__)

                # cache_reload should be able to update the cache once daily,
                # so try out not doing a cache update as the updated_on only gets updated if there is an update
                # if there isn't an update then it doesn't get updated which means that the cache will always be called
                # revisit 2024/05/01
                #
                # if data is not None and dkwargs.get('update_daily'):
                #     updated_on = Cache.get_updated_on(f.__name__)
                #     kwargs['func'] = f
                #     if 'decorator' in dkwargs:
                #         kwargs['decorator'] = dkwargs['decorator']
                #     if 'sort_by' in dkwargs:
                #         kwargs['sort_by'] = dkwargs['sort_by']
                #     if (datetime.utcnow() - updated_on).total_seconds() > 60*60*24:  # update pages once a day
                #         update_cache(*args, **kwargs)

            if data is None:
                if 'db_call' in dkwargs:
                    data = dkwargs['db_call'](*args, **kwargs)
                else:
                    data = f(*args, **kwargs)
                if 'from_cache' not in dkwargs:
                    Cache.set_data(f.__name__, data)

            return json.loads(data) if type(data) is str else data
        return decorated
    return use_cache_inner


def update_cache(*args, **kwargs):
    func = kwargs.pop('func')
    cache___name__ = func.__name__.replace("_from_db", "")
    cached_data = Cache.get_data(cache___name__)
    if 'decorator' in kwargs:
        func = kwargs['decorator'](func)

    data = func(*args, **kwargs)

    updated = False
    if 'error' in session:
        current_app.logger.info(f'Error from API call {cache___name__}')
        return False
    elif cached_data != data:
        current_app.logger.info('Cache updated from db')
        Cache.set_data(cache___name__, data)
        updated = True
    else:
        current_app.logger.info('Cache does not need updating for {}'.format(func.__name__))

    Cache.purge_older_versions(func.__name__)

    return updated


def is_uuid(_val):
    return _val.count('-') == 4


def set_pending(description, url, method, payload, cache_type, key=None, val=None):
    message = ""
    cache_name = f'pending_{cache_type}s'
    q_item = None

    if method == 'delete':
        q_item = Queue.get_item_by_payload_key(cache_name, key, val)
        if q_item:
            Queue.delete(q_item.hash_item)
            return {
                'id': val,
                'success': True,
                'message': f"Pending {cache_type} deleted"
            }
        else:
            payload[key] = val
            payload['pending'] = 'delete'
            message = f"Pending {cache_type} will be deleted"

    if 'pending' not in payload.keys():
        payload['pending'] = 'add' if description.startswith('add') or \
            key and not is_uuid(val) else 'update'

    if key:
        q_item = Queue.get_item_by_payload_key(cache_name, key, val)
        if q_item:
            q_item.payload = json.dumps(payload)
            Queue.update(q_item)
            message = f'Pending {cache_type} will be updated'

    if not message:
        str_payload = json.dumps(payload)

        if key:
            payload[key] = val
        else:
            hash_id = hashlib.md5(','.join([description, url, method, str_payload]).encode('utf-8')).hexdigest()

            payload['id'] = hash_id

        message = f'{cache_type} {description} will be added'

    if not q_item:
        Queue.add(
            description,
            cache_name=cache_name, cache_type=cache_type,
            url=url, method=method, payload=payload
        )

    return {
        'id': payload['id'],
        'success': True if message else False,
        'message': message or f"Problem updating {cache_type}"
    }


class ApiClient(BaseAPIClient):
    def init_app(self, app):
        super(ApiClient, self).init_app(app)

    def process(self, q_item, override=False):
        if not override and q_item.held_until and (datetime.now() < q_item.held_until):
            return {
                "success": False,
                "message": f"Cannot process {q_item.hash_item} until {q_item.held_until}"
            }

        payload = json.loads(q_item.payload) if q_item.payload.startswith('{') else q_item.payload

        if q_item.method.lower() == 'post':
            _payload = {}
            if q_item.cache_type == 'event':
                # ignore fields which are normally returned for convenience
                # cannot be processed during update
                ignore_fields = ['event_type', 'speakers', 'venue']
                keys = payload.keys()
                for k in keys:
                    if k not in ignore_fields:
                        _payload[k] = payload[k]
            else:
                _payload = payload
            json_resp = self.post(
                url=q_item.url,
                data=_payload,
                headers=json.loads(q_item.headers) if q_item.headers else None
            )
        elif q_item.method.lower() == 'delete':
            json_resp = self.delete(
                url=q_item.url
            )
        else:
            json_resp = self.get(url=q_item.url)

        if 'error' in session:
            q_item.status = "error"
            error = session.pop('error')
            q_item.response = json.dumps(error)
            if q_item.retry_count is None:
                q_item.retry_count = 0
            else:
                q_item.retry_count += 1
            Queue.update(q_item)
            return error
        else:
            if q_item.cache_name:
                Cache.set_data(q_item.cache_name, json_resp, is_unique=q_item.cache_is_unique)

            q_item.status = "ok"
            q_item.response = json.dumps(json_resp)

        if q_item.cache_type == 'event':
            cache = Cache.get_cache('get_limited_events')
            found = False
            json_response = json.loads(q_item.response)
            json_cache = json.loads(cache['data'])
            delete_index = -1
            for i, c in enumerate(json_cache):
                if c['id'] == payload['id']:
                    if q_item.method == 'delete':
                        delete_index = i
                    else:
                        json_cache[i] = json_response
                    found = True
                    break
            if not found:
                if q_item.method == 'delete':
                    current_app.logger.error(f'event {q_item} not found in limited_events')
                else:
                    json_cache.insert(0, json_response)
            elif q_item.method == 'delete':
                del json_cache[delete_index]
            Cache.set_data('get_limited_events', json_cache, is_unique=True)
            session['events'] = json_cache

            Queue.add('get future event post-process', url='events/future', method='get')
            Queue.add('get past event post-process', url='events/past_year', method='get')

        Queue.update(q_item)

        return json_resp

    def get_speakers_from_db(self):
        return self.get(url='speakers')

    @use_cache(db_call=get_speakers_from_db)
    def get_speakers(self):
        return self.get_speakers_from_db()

    def add_speaker(self, name):
        data = {'name': name}

        return self.post(url='speaker', data=data)

    def get_venues_from_db(self):
        return self.get(url='venues')

    @use_cache(db_call=get_venues_from_db)
    def get_venues(self):
        return self.get_venues_from_db()

    def get_venue_by_id(self, venue_id):
        return self.get(url='venue/{}'.format(venue_id))

    def add_event(self, event):
        return set_pending(
            f'add event {event["title"]}', 'event', 'post', event, 'event'
        )

    def delete_event(self, event_id):
        event = self.get_event_by_id(event_id)
        return set_pending(
            f'delete event {event_id}', f'event/{event_id}', 'delete', event, 'event', key="id", val=str(event_id)
        )

    def update_event(self, event_id, event):
        return set_pending(
            f'update event {event["title"]}',
            f'event/{event_id}' if is_uuid(event_id) else 'event',
            'post', event, 'event', key="id", val=event_id
        )

    def sync_paypal(self, event_id):
        self.get(url='event/sync_paypal/{}'.format(event_id))

    def get_event_by_id_from_db(self, event_id):
        return self.get(url='event/{}'.format(event_id))

    @use_cache(
        db_call=get_event_by_id_from_db,
        from_cache='get_limited_events',
        key='id')
    def get_event_by_id(self, event_id):
        return get_nice_event_date(self.get_event_by_id_from_db(event_id))

    def get_event_by_old_id(self, event_id):
        event = self.get(url='legacy/event_handler?eventid={}'.format(event_id))
        if event:
            return self.get_nice_event_date(event)

    def get_event_types_from_db(self):
        return self.get(url='event_types')

    @use_cache(db_call=get_event_types_from_db)
    def get_event_types(self):
        return self.get_event_types_from_db()

    def get_limited_events_from_db(self):
        return get_nice_event_dates(self.get(url='events/limit/30'))

    @use_cache(db_call=get_limited_events_from_db)
    def get_limited_events(self):
        return self.get_limited_events_from_db()

    def get_pending_and_limited_events(self):
        _pending_events = Queue.get_by_cache_name('pending_events')
        pending_events = [json.loads(e.payload) for e in _pending_events if e.payload != []]
        return pending_events + self.get_limited_events()

    def get_events_in_year(self, year=None):
        if not year:
            year = int(datetime.today().strftime("%Y"))
        return get_nice_event_dates(self.get(url='events/year/{}'.format(year)))

    def get_event_attendance(self, eventdate_id):
        return self.get(url='event/tickets_and_reserved/' + eventdate_id)

    def get_latest_magazine_from_db(self):
        return self.get(url='magazine/latest')

    @use_cache(db_call=get_latest_magazine_from_db)
    def get_latest_magazine(self):
        return self.get(url='magazine/latest')

    @only_show_approved_events
    def get_events_in_future_from_db(self):
        events = get_nice_event_dates(self.get(url='events/future'), future_dates_only=True)
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
        return get_nice_event_dates(self.get(url='events/past_year'))

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

    def get_articles_from_db(self):
        return self.get(url='articles')

    def get_articles_summary_from_db(self):
        return self.get(url='articles/summary')

    @use_cache(update_daily=True, db_call=get_articles_summary_from_db)
    def get_articles_summary(self):
        return self.get_articles_summary_from_db()

    def get_article_from_db(self, id):
        article = self.get(url='article/{}'.format(id))
        return article

    @sim_data_available()
    def get_article(self, id):
        return self.get(url='article/{}'.format(id))

    def update_article(self, id, article):
        article.pop('article_id')
        return self.post(url='article/{}'.format(id), data=article)

    def add_article(self, article):
        return self.post(url='article', data=article)

    def upload_articles_zipfile(self, article):
        return self.post(url='articles/upload', data=article)

    def get_books_from_db(self):
        return self.get(url='books')

    @use_cache(db_call=get_books_from_db)
    def get_books(self):
        return self.get_books_from_db()

    def get_book(self, id):
        return self.get(url='book/{}'.format(id))

    def get_order(self, txn_code):
        return self.get(url='order/{}'.format(txn_code))

    def update_order(self, txn_id, delivery_sent, refund_issued, notes):
        data = {
            'delivery_sent': delivery_sent,
            'refund_issued': refund_issued,
            'notes': notes,
        }

        return self.post(url='order/{}'.format(txn_id), data=data)

    def get_orders(self, year=None):
        if not year:
            year = datetime.now().year
        return self.get(url='orders/{}'.format(year))

    def replay_confirmation_email(self, txn_id):
        return self.get(url=f'orders/replay_confirmation_email/{txn_id}')

    def add_magazine(self, magazine):
        return self.post(url='magazine', data=magazine)

    def update_magazine(self, id, magazine):
        return self.post(url='magazine/{}'.format(id), data=magazine)

    def get_magazine(self, id):
        return self.get(url='magazine/{}'.format(id))

    def get_magazines_from_db(self):
        return self.get(url='magazines')

    @use_cache(update_daily=True, db_call=get_magazines_from_db)
    def get_magazines(self):
        return self.get_magazines_from_db()

    def get_member_from_unsubcode(self, unsubcode):
        return self.get(url='member/{}'.format(unsubcode))

    def get_member_from_email_address(self, email_address):
        return self.get(url='member/email/{}'.format(email_address))

    def unsubscribe_member(self, unsubcode):
        Queue.add('unsubscribe member', url=f'member/unsubscribe/{unsubcode}', method='post')
        return json.dumps({'message': 'Your unsubscription will be processed'})

    def update_member_by_admin(self, unsubcode, name, email, active):
        data = {
            'name': name,
            'email': email,
            'active': active
        }
        return self.post(url='member/update/{}'.format(unsubcode), data=data)

    def update_member(self, unsubcode, name, email):
        data = {
            'name': name,
            'email': email
        }
        return self.post(url='member/update/{}'.format(unsubcode), data=data)

    def update_order_address(self, txn_id, street, city, state, postcode, country_code, country_name):
        data = {
            'address_street': street,
            'address_city': city,
            'address_state': state,
            'address_postal_code': postcode,
            'address_country_code': country_code,
            'address_country': country_name,
        }
        return self.post(url='order/update_address/{}'.format(txn_id), data=data)

    def get_marketings(self):
        return self.get(url='marketings')

    def get_user(self, email):
        users = Cache.get_data('get_users', default=[])

        for user in users:
            if 'email' in user and user['email'] == email:
                return user

        user = self.get(url='user/{}'.format(email))
        if user:  # in case there was an error response from the API
            users.append(user)

        Cache.set_data('get_users', users, is_unique=True)

        return user

    def get_users_from_db(self):
        return self.get(url='users')

    def get_users(self):
        Queue.add(
            'get users', url='users', method='get', backoff_duration=30,
            cache_name="get_users", cache_is_unique=True)
        return Cache.get_data('get_users', default=[])

    def create_user(self, profile):
        data = {
            'email': profile['email'],
            'name': profile['name'],
        }
        resp = self.post(url='user', data=data)
        Queue.add(
            'get users', url='users', method='get', backoff_duration=30,
            cache_name="get_users", cache_is_unique=True, replace=True)
        return resp

    def update_user_access_area(self, user_id, access_area):
        data = {
            'access_area': access_area
        }
        resp = self.post(url='user/{}'.format(user_id), data=data)
        Queue.add(
            'get users', url='users', method='get', backoff_duration=30,
            cache_name="get_users", cache_is_unique=True, replace=True)
        return resp

    def add_subscription_email(self, name, email, marketing_id):
        data = {
            'name': name,
            'email': email,
            'marketing_id': marketing_id
        }

        Queue.add(f'subscribe {name}', url='member/subscribe', method='post', payload=data)
        return json.dumps({'message': 'Your subscription will be processed'})

    def send_message(self, name, email, reason, message):
        data = {
            'name': name,
            'email': email,
            'reason': reason,
            'message': message,
        }

        Queue.add('send message from web form', url='send_message', method='post', payload=data)
        return json.dumps({'message': 'Your message will be sent'})

    def reserve_place(self, name, email, eventdate_id):
        data = {
            'name': name,
            'email': email,
            'eventdate_id': eventdate_id
        }

        Queue.add(f'reserve place for {name}', url='event/reserve', method='post', payload=data)
        return json.dumps({'message': 'Your place will be reserved'})

    def test_api(self):
        return self.get(url="/")
