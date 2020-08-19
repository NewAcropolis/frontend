import os

from functools import wraps
from flask import current_app, redirect, render_template, request, Response, session, url_for
import requests
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError

from app import api_client
from app.main import main
from app.main.forms import ContactForm, SlimSubscriptionForm
from app.clients.errors import HTTPError

# OAuth endpoints given in the Google API documentation
authorization_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
token_url = "https://www.googleapis.com/oauth2/v4/token"
user_info_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
revoke_token_url = 'https://accounts.google.com/o/oauth2/revoke'
scope = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]


def check_auth(username, password):
    return username == current_app.config['AUTH_USERNAME'] and password == current_app.config['AUTH_PASSWORD']


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def requires_google_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get('oauth_token')
        state = session.get('oauth_state')

        if token and state:
            try:
                google = OAuth2Session(current_app.config['GOOGLE_OAUTH2_CLIENT_ID'], token=token)
                google.get('https://www.googleapis.com/oauth2/v3/tokeninfo')
            except TokenExpiredError:
                del session['oauth_token']

        if not token:
            return google_login()
        return f(*args, **kwargs)
    return decorated


def google_login():
    google = OAuth2Session(
        current_app.config['GOOGLE_OAUTH2_CLIENT_ID'],
        scope=scope,
        redirect_uri=current_app.config['GOOGLE_OAUTH2_REDIRECT_URI']
    )
    authorization_url, state = google.authorization_url(authorization_base_url)

    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    session['target_url'] = request.url

    return redirect(authorization_url)


@main.route("/oauth2callback", methods=["GET"])
def callback():
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = current_app.config['OAUTHLIB_INSECURE_TRANSPORT']

    google = OAuth2Session(
        current_app.config['GOOGLE_OAUTH2_CLIENT_ID'],
        state=session.get('oauth_state'),
        redirect_uri=current_app.config['GOOGLE_OAUTH2_REDIRECT_URI']
    )

    token = google.fetch_token(
        token_url,
        client_secret=current_app.config['GOOGLE_OAUTH2_CLIENT_SECRET'],
        authorization_response=request.url
    )

    auth_google = OAuth2Session(current_app.config['GOOGLE_OAUTH2_CLIENT_ID'], token=token)

    profile = auth_google.get(user_info_url).json()

    user = api_client.get_user(profile['email'])

    if not user:
        try:
            api_client.create_user(profile)

            if 'error' in session:
                error = session.pop('error')
                raise HTTPError(error)

            return render_template(
                'views/admin/admin_interstitial.html',
                message="{} has registered as a user, "
                "please wait until the web administrators setup your permissions".format(profile['email'])
            )
        except HTTPError as e:
            if 'not in correct domain' in e.message:
                return render_template(
                    'views/admin/admin_interstitial.html',
                    message='{}, please contact the website administrators to get an email in correct domain'.format(
                        e.message)
                )
            raise
    elif not user.get('access_area'):
        return render_template(
            'views/admin/admin_interstitial.html',
            message='Waiting for permissions to be granted for {} by website administrators'.format(profile['email'])
        )
    else:
        session['user'] = user

    session['oauth_token'] = token

    # store profile in session to use later
    session['user_profile'] = profile

    return redirect(session.pop('target_url', url_for('.admin')))


@main.route('/logout')
def logout():
    if session.get('user_profile'):
        del session['user_profile']
        del session['user']
        requests.post(
            revoke_token_url,
            params={'token': session.pop('oauth_token')},
            headers={'content-type': 'application/x-www-form-urlencoded'}
        )

    return redirect(url_for('.index'))


@main.route('/_keep_alive', methods=['GET'])
def keep_alive():
    api_client.get_info()

    return 'API called'


def render_page(template, **kwargs):
    contact_form = ContactForm()
    contact_form.setup()

    slim_subscription_form = SlimSubscriptionForm()

    if slim_subscription_form.validate_on_submit():
        return redirect(url_for('main.subscription', email=slim_subscription_form.slim_subscription_email.data))

    if 'error' in session and 'error' not in kwargs:
        error = session.pop('error')
        kwargs['error'] = error['message']['error'] if isinstance(error, dict) else\
            error['message'] if 'message' in error else\
            error if isinstance(error, basestring) else "Unhandled error"

    if 'latest_magazine' not in session:
        latest_magazine = api_client.get_latest_magazine()
        session['latest_magazine'] = latest_magazine
    else:
        latest_magazine = session['latest_magazine']

    return render_template(
        template,
        contact_form=contact_form,
        slim_subscription_form=slim_subscription_form,
        latest_magazine=latest_magazine,
        **kwargs
    )
