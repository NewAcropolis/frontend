from flask import Blueprint

main = Blueprint('main', __name__)  # noqa

from app.main.views import (  # noqa
    index, articles, api, e_shop, events, magazines, member, subscription
)

from app.main.views.admin import (  # noqa
    admin, events, emails, magazines
)
