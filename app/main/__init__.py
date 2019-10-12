from flask import Blueprint

main = Blueprint('main', __name__)  # noqa

from app.main.views import (  # noqa
    index, articles, api, subscription
)

from app.main.views.admin import (  # noqa
    admin, events, emails
)
