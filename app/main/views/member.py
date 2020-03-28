from flask import request
from app.main.forms import UnsubscribeForm, UpdateMemberForm
from app.main import main
from app.main.views import render_page
from app import api_client


@main.route('/member/unsubscribe/<unsubcode>', methods=['GET', 'POST'])
def unsubscribe(unsubcode):
    message = error = ''
    member = api_client.get_member_from_unsubcode(unsubcode)

    unsubscribe_form = UnsubscribeForm()

    if not member['active']:
        message = '{} has already unsubscribed'.format(member['name'])

    if unsubscribe_form.validate_on_submit():
        if unsubscribe_form.email.data == member['email']:
            response = api_client.unsubscribe_member(unsubcode)
            if 'message' in response:
                message = response['message']
        else:
            error = 'Email does not match members email'

    return render_page(
        'views/unsubscribe.html',
        unsubscribe_form=unsubscribe_form,
        unsubcode=unsubcode,
        member_name=member.get('name') if member else None,
        message=message,
        error=error
    )


@main.route('/member/update/<unsubcode>', methods=['GET', 'POST'])
def update(unsubcode):
    message = error = ''
    member = api_client.get_member_from_unsubcode(unsubcode)

    update_member_form = UpdateMemberForm()

    if update_member_form.validate_on_submit():
        if update_member_form.verify_email.data == member['email']:
            response = api_client.update_member(unsubcode, update_member_form.name.data, update_member_form.email.data)
            if 'message' in response:
                message = response['message']
        else:
            error = 'Email does not match members email'

    return render_page(
        'views/update_member.html',
        update_member_form=update_member_form,
        unsubcode=unsubcode,
        member_name=member.get('name') if member else None,
        message=message,
        error=error
    )


@main.route('/legacy/member', methods=['GET'])
def legacy_member():
    _unsubcode = request.args.get('id').encode("utf8")
    _changeemail = request.args.get('changeemail')
    if _changeemail == 'y':
        return update(_unsubcode)
    else:
        return unsubscribe(_unsubcode)
