from flask import Blueprint

main = Blueprint('main', __name__)  # noqa

from app.main.views import ( # noqa
    index, articles, api, cache, courses, download, events,
    magazines, member, order, queue, shop, subscription,
    tag
)

from app.main.views.admin import (  # noqa
    admin, articles, cache, events, emails, magazines, members, orders, queue
)
