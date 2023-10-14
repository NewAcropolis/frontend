import base64
from datetime import datetime, timedelta
from flask import current_app
from google.cloud import ndb
import hashlib
import json


class Queue(ndb.Model):
    description = ndb.StringProperty()
    method = ndb.StringProperty()
    url = ndb.StringProperty()
    payload = ndb.TextProperty(indexed=False)
    headers = ndb.StringProperty()
    hash_item = ndb.StringProperty()
    status = ndb.StringProperty()
    cache_name = ndb.StringProperty()
    cache_type = ndb.StringProperty()
    cache_is_unique = ndb.BooleanProperty()
    created = ndb.DateTimeProperty(auto_now_add=True, indexed=True)
    updated = ndb.DateTimeProperty(auto_now_add=True, indexed=True)
    response = ndb.TextProperty(indexed=False)
    retry_count = ndb.IntegerProperty(default=0, indexed=True)
    backoff_duration = ndb.IntegerProperty()
    held_until = ndb.DateTimeProperty()

    @staticmethod
    def list_queue(status="all", return_as_string=True):
        if type(status) == list:
            query = Queue.query(ndb.OR(Queue.status == status[0], Queue.status == status[1]))
        elif status != "all":
            query = Queue.query(Queue.status == status)
        else:
            query = Queue.query()

        if return_as_string:
            queue = {}
            for res in query.order(Queue.updated).fetch():
                if res.hash_item not in queue:
                    try:
                        payload = json.loads(res.payload)
                        if 'image_data' in payload.keys():
                            image_data = base64.b64decode(payload['image_data']).decode('utf-8')
                            payload['image_data'] = (
                                f"<img class=\"img-thumbnail\" src=\"data:image/png;base64, {image_data}\" />"
                            )
                    except Exception:
                        payload = res.payload
                    queue[res.hash_item] = {}
                    queue[res.hash_item]['hash_item'] = res.hash_item
                    queue[res.hash_item]['description'] = res.description
                    queue[res.hash_item]['method'] = res.method
                    queue[res.hash_item]['url'] = res.url
                    queue[res.hash_item]['payload'] = payload
                    queue[res.hash_item]['headers'] = res.headers
                    queue[res.hash_item]['created'] = res.created
                    queue[res.hash_item]['updated'] = res.updated
                    queue[res.hash_item]['cache_name'] = res.cache_name
                    queue[res.hash_item]['cache_type'] = res.cache_type
                    queue[res.hash_item]['cache_is_unique'] = res.cache_is_unique
                    queue[res.hash_item]['status'] = res.status
                    queue[res.hash_item]['response'] = res.response
                    queue[res.hash_item]['retry_count'] = res.retry_count
                    queue[res.hash_item]['backoff_duration'] = res.backoff_duration
                    queue[res.hash_item]['held_until'] = res.held_until
                    queue[res.hash_item]['count'] = 1
                else:
                    queue[res.hash_item]['count'] += 1
            return queue
        else:
            return query.order(Queue.updated).fetch()

    @staticmethod
    def purge_expired_items():
        deleted = 0
        datetime_now = datetime.utcnow()
        for q in Queue.query().filter(
            Queue.status == "ok"
        ):
            if datetime_now > q.updated + timedelta(
                minutes=q.backoff_duration if q.backoff_duration else current_app.config["QUEUE_EXPIRY"]
            ):
                q.key.delete()
                deleted += 1

        return deleted

    @staticmethod
    def suspend_error_items():
        suspended = 0
        for q in Queue.query().filter(
            Queue.status == "error",
            Queue.retry_count > current_app.config['QUEUE_RETRY_LIMIT']
        ):
            q.status = "suspend"
            q.put()
            suspended += 1

        return suspended

    @staticmethod
    def add(
        description, url, method,
        payload=None, headers=None, cache_name=None, cache_type=None, cache_is_unique=False, backoff_duration=None,
        replace=False, is_json=True
    ):
        payload_str = json.dumps(payload) if is_json else payload
        headers_str = json.dumps(headers)
        hash_item = hashlib.md5(f"{description}-{url}-{method}-{payload_str}".encode()).hexdigest()
        item = Queue.query(Queue.hash_item == hash_item).get()
        if not item or replace:
            if replace and item:
                Queue.delete(hash_item)

            queue = Queue(
                description=description,
                url=url,
                method=method,
                payload=payload_str,
                headers=headers_str,
                hash_item=hash_item,
                status='new',
                cache_name=cache_name,
                cache_type=cache_type,
                cache_is_unique=cache_is_unique,
                backoff_duration=backoff_duration if backoff_duration else current_app.config['QUEUE_EXPIRY']
            )
            queue.put()
        else:
            current_app.logger.info(f"Item {hash_item}, already queued")

    @staticmethod
    def delete(hash_item):
        items = Queue.query(Queue.hash_item == hash_item).fetch()
        if items:
            for item in items:
                item.key.delete()
            return True
        return False

    @staticmethod
    def get(hash_item):
        q = Queue.query(Queue.hash_item == hash_item).get()

        return q

    @staticmethod
    def update(q_item):
        q_item.put()

    @staticmethod
    def get_by_cache_name(cache_name):
        retval = Queue.query(
            ndb.AND(Queue.cache_name == cache_name, Queue.status == 'new')).order(
            -Queue.updated).fetch()
        if retval:
            return retval
        return []

    @staticmethod
    def set_payload(cache_name, payload):
        _queue = Queue.query(Queue.cache_name == cache_name).get()
        if _queue:
            _queue.payload = json.dumps(payload)
            _queue.put()
            return True
        return False

    @staticmethod
    def hold_off_processing(q_item, minutes=10):
        q_item.held_until = datetime.now() + timedelta(minutes=minutes)
        q_item.put()
        return q_item.held_until

    @staticmethod
    def get_item_by_payload_key(cache_name, key, val):
        queued_data = Queue.get_by_cache_name(cache_name)
        for q in queued_data:
            if json.loads(q.payload)[key] == val:
                return q
