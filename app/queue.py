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
    hash_item = ndb.StringProperty()
    status = ndb.StringProperty()
    cache_name = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True, indexed=True)
    updated = ndb.DateTimeProperty(auto_now_add=True, indexed=True)
    response = ndb.StringProperty()
    retry_count = ndb.IntegerProperty(default=0)

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
                    queue[res.hash_item] = {}
                    queue[res.hash_item]['hash_item'] = res.hash_item
                    queue[res.hash_item]['description'] = res.description
                    queue[res.hash_item]['method'] = res.method
                    queue[res.hash_item]['url'] = res.url
                    queue[res.hash_item]['payload'] = res.payload
                    queue[res.hash_item]['created'] = res.created
                    queue[res.hash_item]['updated'] = res.updated
                    queue[res.hash_item]['cache_name'] = res.cache_name
                    queue[res.hash_item]['status'] = res.status
                    queue[res.hash_item]['response'] = res.response
                    queue[res.hash_item]['retry_count'] = res.retry_count
            return queue
        else:
            return query.order(Queue.updated).fetch()

    @staticmethod
    def purge_expired_items():
        deleted = 0
        for q in Queue.query().filter(
            Queue.status == "ok",
            Queue.updated > datetime.utcnow() + timedelta(minutes=current_app.config['QUEUE_EXPIRY'])
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
    def add(description, url, method, payload):
        payload_str = json.dumps(payload)
        hash_item = hashlib.md5(f"{description}-{url}-{method}-{payload_str}".encode()).hexdigest()
        queue = Queue(
            description=description,
            url=url,
            method=method,
            payload=payload_str,
            hash_item=hash_item,
            status='new'
        )
        queue.put()

    @staticmethod
    def delete(hash_item):
        item = Queue.query(Queue.hash_item == hash_item).get()
        if item:
            item.key.delete()

    @staticmethod
    def get(hash_item):
        q = Queue.query(Queue.hash_item == hash_item).get()

        return q

    @staticmethod
    def update(q_item):
        q_item.put()