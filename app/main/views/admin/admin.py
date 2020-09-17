from flask import current_app, jsonify, render_template, session

from requests_oauthlib import OAuth2Session

from app import api_client
from app.main import main
from app.main.forms import UserListForm
from app.main.views import requires_google_auth


@main.route('/admin')
def admin():
    return render_template(
        'views/admin/admin.html',
        name=session['user_profile']['name']
    )


@main.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    users = [u for u in api_client.get_users() if u.get('access_area') != 'admin']
    form = UserListForm()
    update_count = 0

    if form.validate_on_submit():
        for i, user in enumerate(form.users):
            access_area = ''
            if user.admin.data:
                access_area += 'admin,'
            if user.event.data:
                access_area += 'event,'
            if user.email.data:
                access_area += 'email,'
            if user.magazine.data:
                access_area += 'magazine,'
            if user.shop.data:
                access_area += 'shop,'
            if user.announcement.data:
                access_area += 'announcement,'
            if user.article.data:
                access_area += 'article,'

            if users[i]['access_area'] != access_area:
                update_count += 1
                api_client.update_user_access_area(users[i]['id'], access_area)

    form.populate_user_form(users)

    return render_template(
        'views/admin/users.html',
        users=users,
        update_count=update_count,
        access_areas=current_app.config['ACCESS_AREAS'],
        form=form
    )


@main.route("/profile", methods=["GET"])
@requires_google_auth
def profile():
    """Fetching a protected resource using an OAuth 2 token.
    """

    google = OAuth2Session(current_app.config['GOOGLE_OAUTH2_CLIENT_ID'], token=session['oauth_token'])
    return jsonify(google.get('https://www.googleapis.com/oauth2/v1/userinfo').json())
