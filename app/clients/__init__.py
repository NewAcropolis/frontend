from flask import (
    current_app,
    request,
    session
)
import json
import requests
from urllib.parse import urljoin
import time

from app.clients.errors import HTTPError, InvalidResponse
from app.stats import send_ga_event


class BaseAPIClient(object):
    def init_app(self, app):
        self.base_url = app.config['API_BASE_URL']
        self.client_id = app.config['ADMIN_CLIENT_ID']
        self.secret = app.config['ADMIN_CLIENT_SECRET']

    def post(self, url, data, headers=None):
        return self.request("POST", url, data=data, headers=headers)

    def delete(self, url):
        return self.request("DELETE", url)

    def get(self, url, params=None):
        if 'error' in session:
            del session['error']

        return self.request("GET", url, params=params)

    def generate_headers(self, api_token):
        return {
            "Content-type": "application/json",
            "Authorization": "Bearer {}".format(api_token)
        }

    def set_access_token(self):
        if not self.base_url:
            current_app.logger.info("No API URL")
            return False

        send_ga_event('frontend', 'visit', request.remote_addr)

        current_app.logger.info("set access token")
        auth_payload = {
            "username": self.client_id,
            "password": self.secret
        }

        auth_url = urljoin(str(self.base_url), "auth/login")
        try:
            auth_response = requests.request(
                "POST",
                auth_url,
                data=json.dumps(auth_payload),
                headers={'Content-Type': 'application/json'},
                allow_redirects=False,
                timeout=60
            )
            auth_response.raise_for_status()
        except (requests.RequestException, requests.Timeout) as e:
            api_error = HTTPError.create(e)
            current_app.logger.error(
                "Set access token: {} failed with {} '{}' - '{}'".format(
                    auth_url,
                    api_error.status_code,
                    api_error.message,
                    e.message
                )
            )
            # raise api_error
            session["error"] = u"Error connecting to API: " +\
                str(e).replace(current_app.config['API_BASE_URL'], 'https://API')
            return False

        session["access_token"] = auth_response.json()["access_token"]
        return True

    def request(self, method, url, data=None, params=None, headers=None):
        current_app.logger.info("API request {} {}".format(method, url))

        # don't set access token for API call to info
        set_access_token = url != ''
        if not self.base_url:
            current_app.logger.info("No API URL")
            return []

        if set_access_token and "access_token" not in session:
            if not self.set_access_token():
                return []

        payload = data if not isinstance(data, dict) else json.dumps(data)

        url = urljoin(str(self.base_url), str(url))
        _headers = {'Authorization': 'Bearer {}'.format(session["access_token"])} if set_access_token else {}
        if headers:
            _headers.update(headers)
        start_time = time.time()
        try:
            response = requests.request(
                method,
                url,
                data=payload,
                params=params,
                headers=_headers,
                timeout=30
            )

            if response.status_code == 404:
                current_app.logger.warn('%r: 404 - %r', url, response.json()['message'])

                session['error'] = {
                    'code': 404,
                    'response': {'error': response.json()}
                }

                return

            if response.status_code == 401 and response.json()['message'] == "Signature expired":
                self.set_access_token()
                response = requests.request(
                    method,
                    url,
                    data=payload,
                    params=params,
                    headers={'Authorization': 'Bearer {}'.format(session["access_token"])}
                )

            response.raise_for_status()
        except requests.RequestException as e:
            api_error = HTTPError.create(e)
            if api_error.status_code in [400, 409] and "Duplicate" in api_error.message:
                current_app.logger.error(
                    "API {} request on {} duplicate with {} '{}'".format(
                        method,
                        url,
                        api_error.status_code,
                        api_error.message
                    )
                )
            else:
                current_app.logger.error(
                    "API {} request on {} failed with {} '{}'".format(
                        method,
                        url,
                        api_error.status_code,
                        api_error.message
                    )
                )
                # raise api_error
                session['error'] = {
                    'code': api_error.status_code,
                    'message': api_error.message or response.json()
                }
                return []
        finally:
            elapsed_time = time.time() - start_time
            current_app.logger.debug("API {} request on {} finished in {}".format(method, url, elapsed_time))

        try:
            if response.status_code == 204:
                return
            return response.json()
        except ValueError:
            raise InvalidResponse(
                response,
                message="No JSON response object could be decoded"
            )
