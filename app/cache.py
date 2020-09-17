from flask import current_app

try:
    from google.appengine.ext import ndb
except Exception:
    from mock import Mock
    ndb = Mock()
    print('Problem importing google.appengine.ext.ndb')


class Cache(ndb.Model):
    name = ndb.StringProperty()
    data = ndb.JsonProperty()
    updated_on = ndb.DateTimeProperty(auto_now_add=True, indexed=True)

    @staticmethod
    def get_data(name, index=0):
        retval = Cache.query(Cache.name == name).order(-Cache.updated_on).fetch(1, offset=index)
        if retval:
            return retval[0].data

    @staticmethod
    def get_updated_on(name):
        retval = Cache.query(Cache.name == name).order(-Cache.updated_on).get()
        if retval:
            return retval.updated_on

    @staticmethod
    def set_data(name, data):
        cache = Cache(name=name, data=data)
        cache.put()

    @staticmethod
    def purge_older_versions(name, num_versions=5):
        cache = {}
        for result in Cache.query(Cache.name == name).order(-Cache.updated_on).fetch(offset=num_versions):
            current_app.logger.info("Deleted: %s - %s", result.name, result.updated_on)
            result.key.delete()
