from app.main import main
from app import api_client
from app.main.views import render_page


@main.route('/article/<uuid:article_id>', methods=['GET', 'POST'])
def article(article_id, **kwargs):
    article = api_client.get_article(article_id)
    return render_page(
        'views/article.html',
        article=article
    )
