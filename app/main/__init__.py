from flask import Blueprint

main = Blueprint('main', __name__)  # noqa

from app.main.views import (  # noqa
    index, articles, api, books, courses, events, member, subscription
)

from app.main.views.admin import (  # noqa
    admin, cache, events, emails, magazines
)
