from google.cloud import ndb

from app import api_client


class Tag(ndb.Model):
    item_id = ndb.StringProperty(indexed=True)
    tag = ndb.StringProperty(indexed=True)
    created_on = ndb.DateTimeProperty(auto_now_add=True)

    @staticmethod
    def get_tags():
        _tags = Tag.query(projection=["tag"], distinct=True)
        tags = []
        for t in _tags.order(Tag.tag).fetch():
            tags.append(t.tag)
        return tags

    @staticmethod
    def get_tags_for_item(item_id):
        _tags = Tag.query(Tag.item_id == item_id)
        tags = []
        for t in _tags.order(Tag.tag).fetch():
            tags.append(t)

        return tags

    @staticmethod
    def add_tag(item_id, tag):
        _tag = Tag.query(Tag.item_id == item_id, Tag.tag == tag).get()
        if not _tag:
            _tag = Tag(item_id=item_id, tag=tag)
            _tag.put()

    @staticmethod
    def reindex(item_type='magazine'):
        num_deleted = num_tags = 0
        for tag in Tag.query().fetch():
            tag.key.delete()
            num_deleted += 1

        if item_type == 'magazine':
            api_call = api_client.get_magazines

        tags = []
        for m in api_call():
            if m['tags']:
                for t in m['tags'].split(','):
                    if t not in tags:
                        tags.append(t)
                        Tag.add_tag(m['id'], t)
                        num_tags += 1

        return {'deleted': num_deleted, 'tags_reindex': num_tags}
