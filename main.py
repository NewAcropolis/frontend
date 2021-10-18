from datetime import datetime
from flask_script import Manager, Server
from app import create_app


app = create_app()

manager = Manager(app)
manager.add_command("runserver", Server(host='0.0.0.0'))


@app.template_filter('strfdate')
def _jinja2_filter_datetime(date, fmt=None):
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    return date_obj.strftime('%A %-d %B')


@manager.command
def list_routes():
    """List URLs of all application routes."""
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        print("{:10} {}".format(", ".join(rule.methods - set(['OPTIONS', 'HEAD'])), rule.rule))


if __name__ == '__main__':
    manager.run()
