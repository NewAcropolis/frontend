from flask import current_app, stream_with_context, Response
import requests

from app.main import main
from app.stats import send_ga_event

CHUNK_SIZE = 5000


@main.route('/download/<string:filename>')
def download(filename):
    def generate():
        url = '{}/pdfs/{}'.format(current_app.config['IMAGES_URL'], filename)
        r = requests.get(url, stream=True)
        for chunk in r.iter_content(CHUNK_SIZE):
            yield chunk

    send_ga_event("magazine_download", "download", filename)
    return Response(stream_with_context(generate()),
                    content_type='application/pdf')
