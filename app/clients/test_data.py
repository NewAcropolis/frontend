from datetime import datetime, timedelta
from flask import current_app

from app.clients.utils import get_nice_event_date


INTRO_COURSE = {
    "booking_code": "9EKLHHDYSVMBQ",
    "conc_fee": 3,
    "description": "&lt;p&gt;Philosophy means love of wisdom (philo-sophia) and is an active attitude of awareness "
                   "towards life. In this sense, we are all born philosophers, with an innate need to ask questions "
                   "and with the intuition that there are answers to be found.\r\nEvery civilization has passed on to "
                   "us its experience and understanding of life.However, most of us have had little opportunity to "
                   "learn about the vast heritage of ideas that have inspired and guided humanity throughout history."
                   "&lt;/p&gt;\r\n&lt;p&gt;This 16-week course will introduce you to the major concepts of Eastern and "
                   "Western Philosophy and explore their relevance and practical application for our lives.&lt;/p&gt;"
                   "\r\n\r\n&lt;h2&gt;Course Framework&lt;/h2&gt;&lt;br&gt;\r\n\r\n&lt;strong&gt;Ethics: Understanding "
                   "yourself&lt;/strong&gt;&lt;br&gt;\r\n\r\nEthics enquires about moral principles and the impact of "
                   "individuals on their environment. But it is also related to happiness, as it helps us to find the "
                   "right &#x27;inner attitude&#x27; to deal with different "
                   "life situations in ways that are beneficial to ourselves and to others.  &lt;br&gt;&lt;br&gt;\r\n\r"
                   "\n&lt;strong&gt;Sociopolitics: Living together in harmony with others&lt;/strong&gt;&lt;br&gt;\r\n"
                   "\r\nSociopolitics looks at relationships in society, both between individuals and between the "
                   "individual and the group. It is concerned with finding principles by which we can create "
                   "harmonious communities where everyone can flourish.&lt;br&gt;&lt;br&gt;\r\n\r\n&lt;strong&gt;"
                   "Philosophy of History: Being part of something greater&lt;/strong&gt;&lt;br&gt;\r\n\r\nWe are all "
                   "products of history and at the same time we all contribute to making history. Philosophy of "
                   "History seeks wisdom in the study of the past and how to apply the lessons of history "
                   "to the present.&lt;br&gt;&lt;br&gt;\r\n\r\n&lt;strong&gt;Philosophy for Living: Practical "
                   "Application&lt;/strong&gt;&lt;br&gt;\r\n\r\nWhat is the value of thinking without action? Action "
                   "is the real measure of what we are, theory and practice inform each other. Each course evening "
                   "will explore the practical relevance of philosophy and its potential to transform ourselves and "
                   "society.&lt;br&gt;&lt;br&gt;\r\n\r\n&lt;strong&gt;\r\nFirst introductory evening FREE. Price for "
                   "the whole course £220 (£150 concessions), handouts included.&lt;/strong&gt;",
    "event_dates": [
        {
            "end_time": "00:00",
            "event_datetime": "2022-06-11 19:00",
            "id": "4ebca0f9-06f5-47f4-af90-8d8dc1daecc6",
            "speakers": [],
            "event_time": "19:00"
        },
        {
            "end_time": "00:00",
            "event_datetime": "2022-06-18 19:00",
            "id": "4ebca0f9-06f5-47f4-af90-8d8dc1daecc6",
            "speakers": [],
            "event_time": "19:00"
        }
    ],
    "event_state": "approved",
    "event_type": "Introductory Course",
    "fee": 5,
    "has_expired": False,
    "image_filename": "2020/4d4b7a69-185e-49f9-8161-2df14a1b9427",
    "multi_day_conc_fee": 0,
    "multi_day_fee": 0,
    "old_id": None,
    "reject_reasons": [],
    "show_banner_text": True,
    "sub_title": "Philosophies of East and West 3",
    "title": "Discover Philosophy",
    "venue": {
        "address": "19 Compton Terrace N1 2UN, next door to Union Chapel.",
        "default": True,
        "directions": "<div>Bus: Bus routes 4, 19, 30, 43 & 277 stop nearby</div><div>Train: Highbury & Islington "
                      "(Victoria Line), 2 minutes walk</div>",
        "id": "eb8318e9-51f0-421a-82e0-98705ca899a1",
        "name": "Head Branch",
        "old_id": 1
    },
    "formatted_event_datetimes": "Sat 11, Sat 18 of June - 7 PM",
    "dates": [
        "2022-06-11",
        "2022-06-18"
    ],
    "event_monthyear": "June 2022",
    "event_time": "19:00",
    "end_time": "00:00"
}


def get_intro_course(external=False):
    _intro_course = INTRO_COURSE.copy()
    _intro_course['image_filename'] = current_app.config['TEST_INTRO_IMAGE']
    _intro_course['booking_code'] = current_app.config['TEST_INTRO_BOOKING']

    n = 0
    for d in _intro_course['event_dates']:
        d['event_datetime'] = datetime.strftime(datetime.now() + timedelta(days=n + 1), "%Y-%m-%d 19:00")
        n += 1

    _intro_course = get_nice_event_date(_intro_course)

    if external:
        _intro_course = INTRO_COURSE.copy()
        _intro_course['booking_code'] = ''
        _intro_course['fee'] = -2
        _intro_course['conc_fee'] = 0
        return _intro_course
    else:
        return _intro_course
