from flask import render_template
from app.main import main
from app import api_client
from app.main.decorators import setup_subscription_form


@main.route('/article/<uuid:article_id>', methods=['GET', 'POST'])
@setup_subscription_form
def article(article_id, **kwargs):
    article = api_client.get_article(article_id)
    return render_template(
        'views/article.html',
        article=article
    )
