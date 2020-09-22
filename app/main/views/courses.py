from flask import current_app, request
import os

from app import api_client
from app.main import main
from app.main.views import render_page


@main.route('/courses')
def courses():
    future_events = api_client.get_events_in_future(approved_only=True)
    intro_courses = [e for e in future_events if e['event_type'] == 'Introductory Course']
    return render_page('views/courses.html', intro_courses=intro_courses)


@main.route('/course_details')
def course_details():
    TOPIC_PATH = os.path.join(current_app.static_folder, "images/topics/")
    topic = request.args.get('topic')

    topic_static_filenames = os.listdir(TOPIC_PATH)
    topic_images = sorted([f for f in topic_static_filenames if f.startswith(topic)])

    if not topic_images:
        topic_images = ["topic_1.png", "topic_2.png", "topic_3.png", "topic_3.png"]

    return render_page('views/course_details.html', topic_images=topic_images)
