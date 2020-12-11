from flask import current_app
import requests


def send_ga_event(category, action, label, value=1):
    payload = {
        'v': 1,
        'tid': current_app.config['GA_ID'],
        'cid': 888,
        't': 'event',
        'ec': category,
        'ea': action,
        'el': label,
        'ev': value
    }

    r = requests.post("http://www.google-analytics.com/collect", data=payload)
    if r.status_code != 200:
        current_app.logger.info("Failed to track {} - {}".format(category, label))
    else:
        current_app.logger.info("Failed to track {} - {}".format(category, label))
