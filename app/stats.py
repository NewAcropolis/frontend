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

    if current_app.config['ENABLE_STATS']:
        headers = {'User-Agent': 'NA-API-Stats'}

        r = requests.post("https://www.google-analytics.com/collect", data=payload, headers=headers)

        if r.status_code != 200:
            current_app.logger.info("Failed to track stats: {}".format(payload))
        else:
            current_app.logger.info("Tracking stats: {}".format(payload))
    else:
        current_app.logger.info("Stats disabled, would have tracked: {}".format(payload))
