import base64
from flask import current_app, jsonify, redirect, render_template, request, session, url_for
import json

from app import api_client
from app.tag import Tag
from app.clients.errors import HTTPError
from app.main import main
from app.main.forms import MemberForm


@main.route('/admin/members', methods=['GET', 'POST'])
def admin_members():
    errors = []
    message = ''

    form = MemberForm()

    if form.validate_on_submit():
        member = {
            'email_address': form.email_address.data,
            'name': form.name.data,
            'active': form.active.data,
        }
        api_client.update_member_by_admin(
            form.unsubcode.data, member['name'], member['email_address'], member['active'])
        if 'error' not in session:
            message = 'member updated'
        else:
            errors = session.pop('error')
            message = 'error updating member'

    return render_template(
        'views/admin/members.html',
        errors=errors,
        form=form,
        message=message,
    )


@main.route('/admin/member/email', methods=['GET', 'POST'])
def _get_member():
    response = api_client.get_member_from_email_address(request.args.get("email"))

    if 'error' in session:
        return session.pop('error'), 404
    else:
        return response
