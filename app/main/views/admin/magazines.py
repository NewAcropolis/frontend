import base64
from flask import current_app, jsonify, redirect, render_template, request, session, url_for
import json

from app import api_client
from app.tag import Tag
from app.clients.api_client import update_cache
from app.clients.errors import HTTPError
from app.main import main
from app.main.forms import MagazineForm
from app.clients.utils import upload_blob_from_base64string


@main.route('/admin/magazines', methods=['GET', 'POST'])
@main.route('/admin/magazines/<uuid:selected_magazine_id>', methods=['GET', 'POST'])
@main.route('/admin/magazines/<uuid:selected_magazine_id>/<api_message>', methods=['GET', 'POST'])
def admin_magazines(selected_magazine_id=None, api_message=None):
    errors = []
    magazines = api_client.get_magazines_from_db()

    form = MagazineForm()

    form.set_magazine_form(magazines)

    tags = Tag.get_tags()

    if form.validate_on_submit():
        if form.magazine_filename.data:
            filename = form.magazine_filename.data.filename
        else:
            filename = form.existing_magazine_filename.data

        magazine = {
            'magazine_id': form.magazines.data,
            'title': form.title.data,
            'filename': filename,
            'topics': form.topics.data,
            'tags': form.tags.data
        }

        file_request = request.files.get('magazine_filename')
        if file_request:
            file_data = file_request.read()
            file_data_encoded = base64.b64encode(file_data)

            magazine['pdf_data'] = base64.b64encode(file_data_encoded).decode('utf-8')

            upload_blob_from_base64string(filename, f"pdf_test/{filename}", file_data_encoded)
        try:
            message = None
            if magazine.get('magazine_id'):
                response = api_client.update_magazine(magazine['magazine_id'], magazine)
                if 'error' not in session:
                    message = 'magazine updated'
                    if form.old_tags.data != form.tags.data:
                        for t in form.tags.data.split(","):
                            if t not in tags:
                                Tag.add_tag(magazine['magazine_id'], t)
                else:
                    api_message = ''
            else:
                response = api_client.add_magazine(magazine)
                message = 'magazine added, please wait a few minutes for the upload to complete'
                update_cache(func=api_client.get_latest_magazine_from_db)

            if 'error' in session:
                errors = session.pop('error')
            else:
                return redirect(
                    url_for('main.admin_magazines', selected_magazine_id=response['id'], api_message=message))
        except HTTPError as e:
            current_app.logger.error(e)
            errors = json.dumps(e.message)
    return render_template(
        'views/admin/magazines.html',
        errors=errors,
        form=form,
        message=api_message,
        selected_magazine_id=selected_magazine_id,
        tags=",".join(tags)
    )


@main.route('/admin/_get_magazine')
def _get_magazine():
    id = request.args.get('magazine_id')

    magazine = api_client.get_magazine(id)
    return jsonify(magazine)
