import os
from flask import current_app, jsonify, render_template, redirect, request, session, url_for

from requests_oauthlib import OAuth2Session

from app.main import main
from app import api_client
from app.main.views import requires_google_auth


@main.route('/admin')
@requires_google_auth
def admin():
    return render_template(
        'views/admin.html',
    )


@main.route("/profile", methods=["GET"])
@requires_google_auth
def profile():
    """Fetching a protected resource using an OAuth 2 token.
    """

    google = OAuth2Session(current_app.config['GOOGLE_OAUTH2_CLIENT_ID'], token=session['oauth_token'])
    return jsonify(google.get('https://www.googleapis.com/oauth2/v1/userinfo').json())


# Add a logout handler.
@main.route('/admin/logout')
def admin_logout():
    # Delete the user's profile and the credentials stored by oauth2.
    del session['oauth_token']
    session.modified = True
    return redirect(request.referrer or '/')