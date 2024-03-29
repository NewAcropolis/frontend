from flask import current_app, jsonify

from app import api_client
from app.main import main
from app.main.views import requires_auth, app_engine_only
from app.queue import Queue


@main.route('/queue/process', methods=['GET'])
@app_engine_only
def process_queue():
    ok = 0
    error = 0
    for q in Queue.list_queue(["new", "error"], return_as_string=False):
        api_client.process(q)
        if q.status == "ok":
            ok += 1
        else:
            error += 1

    return jsonify({"ok": ok, "error": error})


@main.route('/queue/purge', methods=['GET'])
@app_engine_only
def purge_queue():
    current_app.logger.info('Purging queue')
    return jsonify({"deleted": Queue.purge_expired_items()})


@main.route('/queue/suspend_error_items', methods=['GET'])
@app_engine_only
def suspend_error_items():
    return jsonify({"suspended": Queue.suspend_error_items()})


@main.route('/queue', methods=['GET'])
@main.route('/queue/status/<string:status>', methods=['GET'])
@requires_auth
def show_queue(_type=None, status="new"):
    queue = Queue.list_queue(status)
    if not _type:
        queue['type'] = "show"
    else:
        queue['type'] = _type
    return jsonify(queue)


@main.route('/queue/add', methods=['GET'])
@requires_auth
def add_queue():
    Queue.add("test", "test/api", "POST", {"test": "test"})
    return show_queue(("add"))

@main.route('/queue/add2', methods=['GET'])
@requires_auth
def add_queue2():
    Queue.add("test2", "test/api2", "POST", {"test": "test2"})
    return show_queue("add2")


@main.route('/queue/delete/<string:hash_item>', methods=['GET'])
@requires_auth
def delete_from_queue(hash_item):
    Queue.delete(hash_item)

    return show_queue("delete")


@main.route('/queue/update', methods=['GET'])
@requires_auth
def update_queue():
    q = Queue.get("27f1daa58b456bb0702bae8575a9ec1e")
    q.status = "error"
    Queue.update(q)
    return show_queue("update")


@main.route('/queue/test_send_message', methods=['GET'])
@requires_auth
def test_send_message():
    return api_client.send_message('test', 'test@newacropolisuk.org', 'test', 'test')
