from flask import current_app
from google.cloud import ndb
import json

from app import api_client


class MagazineTag(ndb.Model):
    magazine_id = ndb.StringProperty(indexed=True)
    tag = ndb.StringProperty(indexed=True)
    created_on = ndb.DateTimeProperty(auto_now_add=True)

    @staticmethod
    def get_tags():
        _tags = MagazineTag.query(projection=["tag"], distinct=True)
        tags = []
        for t in _tags.fetch():
            tags.append(t.tag)
        return tags

    @staticmethod
    def get_tags_for_magazine(magazine_id):
        _tags = MagazineTag.query(MagazineTag.magazine_id == magazine_id)
        tags = []
        for t in _tags.order(MagazineTag.tag).fetch():
            tags.append(t)

        return tags

    @staticmethod
    def add_magazine_tag(magazine_id, tag):
        magazine_tag = MagazineTag.query(MagazineTag.magazine_id == magazine_id, MagazineTag.tag == tag).get()
        if not magazine_tag:
            magazine_tag = MagazineTag(magazine_id=magazine_id, tag=tag)
            magazine_tag.put()

    @staticmethod
    def reindex():
        num_deleted = num_tags = 0
        for magazine_tag in MagazineTag.query().fetch():
            magazine_tag.key.delete()
            num_deleted += 1

        tags = []
        for m in api_client.get_magazines():
            if m['tags']:
                for t in m['tags'].split(','):
                    if t not in tags:
                        tags.append(t)
                        MagazineTag.add_magazine_tag(m['id'], t)
                        num_tags += 1

        return {'deleted': num_deleted, 'tags_reindex': num_tags}
