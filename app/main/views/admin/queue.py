import base64
from flask import jsonify, render_template
import json

from app import api_client
from app.clients.utils import purge_old_tmp_files
from app.queue import Queue
from app.main import main
from app.main.forms import QueueForm


@main.route('/admin/queue', methods=['GET', 'POST'])
def queue():
    form = QueueForm()
    form.setup_status_filter()
    if form.validate_on_submit():
        queue = Queue.list_queue(form.status_filter.data)
    else:
        queue = Queue.list_queue("new")
    return render_template('views/admin/queue.html', queue=queue, form=form)


@main.route('/admin/queue/<string:cache_name>/<string:key>/<string:val>', methods=['GET', 'POST'])
def show_queue_item(cache_name, key, val):
    queue_item = Queue.get_item_by_payload_key(cache_name, key, val)
    payload = json.loads(queue_item.payload)
    if 'image_data' in payload.keys():
        image_data = base64.b64decode(payload['image_data']).decode('utf-8', 'ignore')
        payload['image_data'] = f"<img class='img-thumbnail' src='data:image/png;base64, {image_data}' />"
        queue_item.payload = json.dumps(payload)

    return render_template('views/admin/queue_show.html', q=queue_item)


@main.route('/admin/queue/tmp/purge', methods=['GET'])
def tmp_purge():
    response = purge_old_tmp_files()
    return jsonify(response)


@main.route('/admin/queue/process/<string:action>/<string:hash_item>')
def process(action, hash_item):
    if action == 'delete':
        Queue.delete(hash_item)

        return 'deleted'
    elif action == 'play':
        q_item = Queue.get(hash_item)
        response = api_client.process(q_item, override=True)

        return jsonify(response)

    elif action == 'suspend':
        q_item = Queue.get(hash_item)
        q_item.status = 'suspend'
        Queue.update(q_item)

    elif action == 'set_new':
        q_item = Queue.get(hash_item)
        q_item.status = 'new'
        Queue.update(q_item)

    return f"{q_item.hash_item} {action}ed"
