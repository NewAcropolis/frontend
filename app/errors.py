from flask import (
    jsonify,
    current_app,
    json)
from flask_wtf.csrf import CSRFError
from jsonschema import ValidationError


def register_errors(blueprint):

    @blueprint.errorhandler(ValidationError)
    def validation_error(error):
        current_app.logger.exception(error)
        return jsonify(json.loads(error.message)), 400

    @blueprint.errorhandler(CSRFError)
    def csrf_error(error):
        current_app.logger.exception(error)
        return jsonify(json.loads(error.message)), 400

    @blueprint.errorhandler(400)
    def bad_request(e):
        msg = e.description or "Invalid request parameters"
        current_app.logger.exception(msg)
        return jsonify(result='error', message=str(msg)), 400

    @blueprint.errorhandler(401)
    def unauthorized(e):
        error_message = "Unauthorized, authentication token must be provided"
        return jsonify(result='error', message=error_message), 401, [('WWW-Authenticate', 'Bearer')]

    @blueprint.errorhandler(403)
    def forbidden(e):
        error_message = "Forbidden, invalid authentication token provided"
        return jsonify(result='error', message=error_message), 403

    # this must be defined after all other error handlers since it catches the generic Exception object
    @blueprint.app_errorhandler(500)
    @blueprint.errorhandler(Exception)
    def internal_server_error(e):
        current_app.logger.exception(e)
        return jsonify(result='error', message="Internal server error"), 500
