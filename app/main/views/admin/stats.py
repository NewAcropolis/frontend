from flask import render_template, request, session

from app import api_client
from app.main import main


@main.route('/admin/stats', methods=['GET'])
def admin_stats():
    errors = []
    message = ''

    return render_template(
        'views/admin/stats.html',
        errors=errors,
        message=message,
    )


@main.route('/admin/stats/fetch', methods=['GET'])
def _fetch_stats():
    response = api_client.get_stats(request.args.get("report_date"), request.args.get("end_report_date"))

    if 'error' in session:
        return session.pop('error'), 404
    else:
        return response
