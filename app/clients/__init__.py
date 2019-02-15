from flask import (
    current_app,
    session
)
import json
import requests
from urlparse import urljoin
import time

from app.clients.errors import HTTPError, InvalidResponse


class BaseAPIClient(object):
    def init_app(self, app):
        self.base_url = app.config['API_BASE_URL']
        self.client_id = app.config['ADMIN_CLIENT_ID']
        self.secret = app.config['ADMIN_CLIENT_SECRET']

    def post(self, url, data):
        return self.request("POST", url, data=data)

    def get(self, url, params=None):
        return self.request("GET", url, params=params)

    def generate_headers(self, api_token):
        return {
            "Content-type": "application/json",
            "Authorization": "Bearer {}".format(api_token)
        }

    def set_access_token(self):
        current_app.logger.info("set access token")
        auth_payload = {
            "username": self.client_id,
            "password": self.secret
        }

        try:
            auth_url = urljoin(str(self.base_url), "auth/login")
            auth_response = requests.request(
                "POST",
                auth_url,
                data=json.dumps(auth_payload),
                headers={'Content-Type': 'application/json'},
                allow_redirects=False
            )
            auth_response.raise_for_status()
        except requests.RequestException as e:
            api_error = HTTPError.create(e)
            current_app.logger.error(
                "Set access token: {} failed with {} '{}'".format(
                    auth_url,
                    api_error.status_code,
                    api_error.message
                )
            )
            raise api_error

        session["access_token"] = auth_response.json()["access_token"]

    def request(self, method, url, data=None, params=None):
        current_app.logger.info("API request {} {}".format(method, url))

        if not session.get("access_token"):
            self.set_access_token()

        payload = json.dumps(data)

        url = urljoin(str(self.base_url), str(url))

        start_time = time.time()
        try:
            response = requests.request(
                method,
                url,
                data=payload,
                params=params,
                headers={'Authorization': 'Bearer {}'.format(session["access_token"])}
            )

            if response.status_code == 404:
                current_app.logger.warn('404', response.json()['message'])
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
            current_app.logger.error(
                "API {} request on {} failed with {} '{}'".format(
                    method,
                    url,
                    api_error.status_code,
                    api_error.message
                )
            )
            raise api_error
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
