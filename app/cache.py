from flask import current_app
from google.cloud import ndb
import json


class Cache(ndb.Model):
    name = ndb.StringProperty()
    # data = ndb.JsonProperty()
    data = ndb.TextProperty(indexed=False)
    updated_on = ndb.DateTimeProperty(auto_now_add=True, indexed=True)

    @staticmethod
    def get_cache_overview():
        cache = {}
        for res in Cache.query().order(-Cache.name).fetch():
            if res.name not in cache:
                cache[res.name] = {}
                cache[res.name]['name'] = res.name
                cache[res.name]['count'] = 1
            else:
                cache[res.name]['count'] += 1

        return cache

    @staticmethod
    def get_data(name, index=0):
        retval = Cache.query(Cache.name == name).order(-Cache.updated_on).fetch(1, offset=index)
        if retval:
            return json.loads(retval[0].data)

    @staticmethod
    def get_updated_on(name):
        retval = Cache.query(Cache.name == name).order(-Cache.updated_on).get()
        if retval:
            return retval.updated_on

    @staticmethod
    def set_data(name, data):
        cache = Cache(name=name, data=json.dumps(data))
        cache.put()

    @staticmethod
    def purge_older_versions(name=None, num_versions=5):
        def _purge_older_versions(_name):
            for result in Cache.query(Cache.name == _name).order(-Cache.updated_on).fetch(offset=num_versions):
                current_app.logger.info("Deleted: %s - %s", result.name, result.updated_on)
                result.key.delete()

        if name:
            _purge_older_versions(name)
        else:
            names = []
            for c in Cache.query().fetch():
                if c.name not in names:
                    names.append(c.name)
                    _purge_older_versions(c.name)

    @staticmethod
    def purge_cache():
        for result in Cache.query().fetch():
            current_app.logger.info("Deleted: %s - %s", result.name, result.updated_on)
            result.key.delete()

    @staticmethod
    def set_review_entity(name, value, key='id'):
        latest = Cache.query(Cache.name == name).order(-Cache.updated_on).get()
        for item in json.loads(latest.data):
            if item[key] == value:
                # remove any other review items that match the key, as there should only be 1 in review
                for r_item in Cache.query(Cache.name == name + "_review").fetch():
                    _r_item = json.loads(r_item.data)
                    if _r_item[key] == value:
                        r_item.key.delete()

                cache = Cache(name=name + "_review", data=json.dumps(item))
                cache.put()
                return
        current_app.logger.info("No matching item found in cache {} to set for {}".format(name, value))

    @staticmethod
    def delete_review_entity(name, value, key='id'):
        for r_item in Cache.query(Cache.name == name + "_review").fetch():
            _r_item = json.loads(r_item.data)
            if _r_item[key] == value:
                r_item.key.delete()
                return
        current_app.logger.info("No matching item found in cache {} to delete for {}".format(name, value))

    @staticmethod
    def get_review_entities(name):
        return Cache.query(Cache.name == name + "_review").order(-Cache.updated_on).fetch()
