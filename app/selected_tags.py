from google.cloud import ndb


class SelectedTags(ndb.Model):
    tags = ndb.StringProperty(indexed=True)
    modified_on = ndb.DateTimeProperty(auto_now_add=True)

    @staticmethod
    def get_selected_tags():
        return SelectedTags.query().get()

    @staticmethod
    def update_selected_tags(tags):
        _selected_tags = SelectedTags.get_selected_tags()
        if _selected_tags:
            _selected_tags.key.delete()

        _tags = SelectedTags(
            tags=tags
        )
        _tags.put()
