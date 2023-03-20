import base64
from flask import current_app, jsonify, redirect, render_template, request, session, url_for
import json

from app import api_client
from app.tag import Tag
from app.clients.api_client import update_cache
from app.clients.errors import HTTPError
from app.main import main
from app.main.forms import ArticleForm
from app.clients.utils import size_from_b64


@main.route('/admin/articles', methods=['GET', 'POST'])
@main.route('/admin/articles/<uuid:selected_article_id>', methods=['GET', 'POST'])
@main.route('/admin/articles/<uuid:selected_article_id>/<api_message>', methods=['GET', 'POST'])
def admin_articles(selected_article_id=None, api_message=None):
    errors = []
    articles = api_client.get_articles_from_db()
    magazines = api_client.get_magazines_from_db()

    form = ArticleForm()

    form.set_article_form(articles, magazines)

    tags = Tag.get_tags()

    if form.validate_on_submit():
        if form.image_filename.data:
            image_filename = form.image_filename.data.filename
        else:
            image_filename = form.existing_image_filename.data

        article = {
            'article_id': form.articles.data,
            'magazine_id': form.magazines.data,
            'title': form.title.data,
            'author': form.author.data,
            'content': form.article_content.data,
            'image_filename': image_filename,
            'tags': form.tags.data,
            'article_state': form.article_state.data,
        }

        file_request = request.files.get('image_filename')

        if file_request:
            file_data = file_request.read()
            file_data_encoded = base64.b64encode(file_data)
            file_data_encoded = base64.b64encode(file_data_encoded).decode('utf-8')
            _file_size = size_from_b64(str(file_data_encoded))
            if _file_size > current_app.config['MAX_IMAGE_SIZE']:
                _file_size_mb = round(_file_size/(1024*1024), 1)
                _max_size_mb = current_app.config['MAX_IMAGE_SIZE']/(1024*1024)
                errors.append("Image {} file size ({} mb) is larger than max ({} mb)".format(
                    file_request.filename, _file_size_mb, _max_size_mb))
            else:
                article['image_data'] = file_data_encoded

        if not errors:
            try:
                message = None
                if article.get('article_id'):
                    article_id = article.get('article_id')
                    response = api_client.update_article(article_id, article)
                    if 'error' not in session:
                        message = 'article updated'
                        if form.old_tags.data != form.tags.data:
                            for t in form.tags.data.split(","):
                                if t not in tags:
                                    Tag.add_tag(article_id, t)
                    else:
                        api_message = ''
                else:
                    response = api_client.add_article(article)
                    message = 'article added, please wait a few minutes for the upload to complete'
                    update_cache(func=api_client.get_articles_summary_from_db)

                if 'error' in session:
                    errors = session.pop('error')
                else:
                    return redirect(
                        url_for('main.admin_articles', selected_article_id=response['id'], api_message=message))
            except HTTPError as e:
                current_app.logger.error(e)
                errors = json.dumps(e.message)
    return render_template(
        'views/admin/articles.html',
        errors=errors,
        form=form,
        message=api_message,
        selected_article_id=selected_article_id,
        tags=",".join(tags)
    )


@main.route('/admin/_get_article')
def _get_article():
    id = request.args.get('article_id')

    article = api_client.get_article(id)

    return jsonify(article)
