import base64
from flask import current_app, jsonify, redirect, render_template, request, session, url_for
import json

from app import api_client
from app.tag import Tag
from app.selected_tags import SelectedTags
from app.clients.api_client import update_cache
from app.clients.errors import HTTPError
from app.main import main
from app.main.forms import ArticleForm, ArticlesZipfileForm, SelectedTagsForm
from app.clients.utils import size_from_b64


@main.route('/admin/articles', methods=['GET', 'POST'])
@main.route('/admin/articles/<uuid:selected_article_id>', methods=['GET', 'POST'])
@main.route('/admin/articles/<uuid:selected_article_id>/<api_message>', methods=['GET', 'POST'])
def admin_articles(selected_article_id=None, api_message=None):
    errors = []
    articles = api_client.get_articles_from_db()
    magazines = api_client.get_magazines_from_db()

    form = ArticleForm()
    selected_tags_form = SelectedTagsForm()

    form.set_article_form(articles, magazines)

    tags = Tag.get_tags()

    if selected_tags_form.active.data == '1' and selected_tags_form.validate_on_submit():
        # breakpoint()
        SelectedTags.update_selected_tags(selected_tags_form.selected_tags.data)
    elif form.validate_on_submit():
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
                    update_cache(func=api_client.get_articles_summary_by_tags_from_db)

                if 'error' in session:
                    errors = session.pop('error')
                else:
                    return redirect(
                        url_for('main.admin_articles', selected_article_id=response['id'], api_message=message))
            except HTTPError as e:
                current_app.logger.error(e)
                errors = json.dumps(e.message)

    if SelectedTags.get_selected_tags():
        selected_tags_form.set_selected_tags_form(SelectedTags.get_selected_tags().tags)

    return render_template(
        'views/admin/articles.html',
        errors=errors,
        form=form,
        selected_tags_form=selected_tags_form,
        message=api_message,
        selected_article_id=selected_article_id,
        tags=",".join(tags)
    )


@main.route('/admin/articles/zipfile', methods=['GET', 'POST'])
def admin_articles_zipfile(zipfile_id=None, api_message=None):
    errors = []
    magazines = api_client.get_magazines_from_db()

    form = ArticlesZipfileForm()

    form.set_articles_zipfile_form(magazines)
    if form.validate_on_submit():
        zipfile_request = request.files.get('articles_zipfile')
        if form.articles_zipfile.data:
            articles_zipfile_filename = form.articles_zipfile.data.filename

            article_zipfile = {
                'magazine_id': form.magazines.data,
                'source_filename': articles_zipfile_filename
            }
            if form.magazines.data:
                article_zipfile['magazine_id']: form.magazines.data

            if zipfile_request:
                file_data = zipfile_request.read()
                file_data_encoded = str(base64.b64encode(file_data), 'utf-8')
                _file_size = size_from_b64(str(file_data_encoded))
                if _file_size > current_app.config['MAX_IMAGE_SIZE']:
                    _file_size_mb = round(_file_size/(1024*1024), 1)
                    _max_size_mb = current_app.config['MAX_IMAGE_SIZE']/(1024*1024)
                    errors.append("Zip {} file size ({} mb) is larger than max ({} mb)".format(
                        zipfile_request.filename, _file_size_mb, _max_size_mb))
                else:
                    article_zipfile['articles_data'] = file_data_encoded

            if not errors:
                try:
                    response = api_client.upload_articles_zipfile(article_zipfile)
                    update_cache(func=api_client.get_articles_summary_by_tags_from_db)
                    if 'errors' in response:
                        errors = '<br>'.join(
                            [f"<a href='/admin/articles/{i['id']}'>{i['article']}</a>" for i in response['errors']]
                        )
                    api_message = '<br>'.join(
                        [f"<a href='/admin/articles/{i['id']}'>{i['name']}</a>" for i in response['articles']]
                    )

                    if 'error' in session:
                        errors = session.pop('error')
                except HTTPError as e:
                    current_app.logger.error(e)
                    errors = json.dumps(e.message)

    return render_template(
        'views/admin/articles_zipfile.html',
        errors=errors,
        form=form,
        message=api_message
    )


@main.route('/admin/_get_article')
def _get_article():
    id = request.args.get('article_id')

    article = api_client.get_article(id)

    return jsonify(article)


@main.route('/admin/_update_selected_tags', methods=['GET', 'POST'])
def _update_selected_tags():
    breakpoint()
    return 'ok'
