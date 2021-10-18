import os

import logging

from google.cloud import ndb


class Settings(ndb.Model):
    name = ndb.StringProperty()
    value = ndb.StringProperty()

    @staticmethod
    def get_or_set(name):
        retval = Settings.query(Settings.name == name).get()
        if not retval:
            logging.info("Setting datastore: {}".format(name))
            retval = Settings(name=name, value=os.environ.get(name, "NOT SET"))
            retval.put()
        return retval.value
