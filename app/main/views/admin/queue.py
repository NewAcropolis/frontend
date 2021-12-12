from flask import jsonify, render_template
import json

from app import api_client
from app.cache import Cache
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


@main.route('/admin/queue/process/<string:action>/<string:hash_item>')
def process(action, hash_item):
    if action == 'delete':
        Queue.delete(hash_item)

        return 'deleted'
    elif action == 'play':
        q_item = Queue.get(hash_item)
        response = api_client.process(q_item)
        if q_item.cache_name:
            Cache.set_data(q_item.cache_name, json.dumps(response))

        return jsonify(response)

    elif action == 'suspend':
        q_item = Queue.get(hash_item)
        q_item.status = 'suspend'
        Queue.update(q_item)

    return f"{q_item.hash_item} {action}ed"
