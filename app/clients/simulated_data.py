from datetime import datetime, timedelta


uuids = [
    '920c7ae0-38c0-4411-9301-7cf14744efdf',
    'd0ef3c1d-8300-40be-ae5c-3b2cfdc7fe50',
    'c0970bcd-8dd1-42c3-89cf-3581126f6566',
    '00ab5d93-b00a-4744-b5e2-9bd85a87dcee',
    '82525576-da4b-469a-923f-601285db5382',
    '7dc6c6ac-31c4-42ae-b346-defdf3432078',
    'a29a8650-42b8-4b4a-8fd9-01b027262fe1',
    'a6f7c24e-8e49-4d5f-9611-7d1cdf504d93'
]


def sim_get_events_in_future(*args, **kwargs):
    future_dates = [
        datetime.strftime(datetime.now() + timedelta(days=n + 1), "%Y-%m-%d 19:00") for n in range(4)
    ]

    simulated_data = [
        {
            "id": uuids[0],
            "title": "Test title",
            "description": "Some description",
            "booking_code": "111222333",
            "event_type": "Talk",
            "image_filename": "event.png",
            "event_dates": [{
                "id": "920c7ae0-38c0-4411-9301-7cf14744efdf",
                "event_datetime": future_dates[0],
                "end_time": None
            }],
            "event_state": "approved",
            "venue": {"name": "London"},
            "show_banner_text": True,
            "fee": 5,
            "conc_fee": 3,
        },
        {
            "id": uuids[1],
            "title": "Test donation",
            "description": "Some description",
            "booking_code": "222333444",
            "event_type": "Talk",
            "image_filename": "event.png",
            "event_dates": [{
                "id": "920c7ae0-38c0-4411-9301-7cf14744efdf",
                "event_datetime": future_dates[1],
                "end_time": "20:30"
            }],
            "event_state": "approved",
            "venue": {"name": "Bristol"},
            "show_banner_text": True,
            "fee": -3
        },
        {
            "id": uuids[2],
            "title": "Test course",
            "description": "Some description",
            "booking_code": "333444555",
            "event_type": "Introductory Course",
            "image_filename": "event.png",
            "event_dates": [{
                "id": "920c7ae0-38c0-4411-9301-7cf14744efdf",
                "event_datetime": future_dates[2],
                "end_time": None
            }],
            "event_monthyear": "January 2019",
            "event_state": "approved",
            "venue": {"name": "London"},
            "show_banner_text": True,
            "fee": 120,
            "conc_fee": 80
        },
        {
            "id": uuids[3],
            "title": "Test title 4",
            "description": "Some description",
            "booking_code": "333444555666",
            "event_type": "Workshop",
            "image_filename": "event.png",
            "event_dates": [{
                "id": "920c7ae0-38c0-4411-9301-7cf14744efdf",
                "event_datetime": future_dates[3],
                "end_time": None
            }],
            "event_state": "approved",
            "venue": {"name": "Online Event"},
            "show_banner_text": True,
            "fee": 5,
            "conc_fee": 3
        },
    ]

    return simulated_data


def sim_get_events_past_year(*args, **kwargs):
    return [
        {
            "id": uuids[4],
            "title": "Test title 5",
            "event_type": "Talk",
            "image_filename": "event.png",
            "event_dates": [{
                "event_datetime": "2018-12-30 19:00",
                "end_time": None
            }],
            "event_state": "approved",
            "venue": {"name": "Online Event"}
        },
        {
            "id": uuids[5],
            "title": "Test title 6",
            "event_type": "Talk",
            "image_filename": "event.png",
            "event_dates": [{
                "event_datetime": "2018-12-31 19:00",
                "end_time": None
            }],
            "event_state": "approved",
            "venue": {"name": "Online Event"}
        },
        {
            "id": uuids[6],
            "title": "Test title 7",
            "event_type": "Introductory Course",
            "image_filename": "event.png",
            "event_dates": [{
                "event_datetime": "2019-01-01 19:00",
                "end_time": None
            }],
            "event_monthyear": "January 2019",
            "event_state": "approved",
            "venue": {"name": "Online Event"}
        },
        {
            "id": uuids[7],
            "title": "Test title 8",
            "event_type": "Workshop",
            "image_filename": "event.png",
            "event_dates": [{
                "event_datetime": "2019-01-02 19:00",
                "end_time": None
            }],
            "event_state": "approved",
            "venue": {"name": "Online Event"}
        },
    ]


def sim_get_event_by_id(*args, **kwargs):
    for e in sim_get_events_in_future():
        if e['id'] == str(args[1]):
            return e


def sim_get_articles_summary(*args, **kwargs):
    return [
        {
            'title': 'Article title 1',
            'short_content':
                'some short content 1, some short content 1, some short content 1, some short content 1',
            'very_short_content': 'some short content 1',
            'image_filename': 'article.png'
        },
        {
            'title': 'Article title 2',
            'short_content':
                'some short content 2, some short content 2, some short content 2, some short content 2',
            'very_short_content': 'some short content 2',
            'image_filename': 'article.png'
        },
        {
            'title': 'Article title 3',
            'short_content':
                'some short content 3, some short content 3, some short content 3, some short content 3',
            'very_short_content': 'some short content 3',
            'image_filename': 'article.png'
        },
        {
            'title': 'Article title 4',
            'short_content':
                'some short content 4, some short content 4, some short content 4, some short content 4',
            'very_short_content': 'some short content 4',
            'image_filename': 'article.png'
        },
        {
            'title': 'Article title 5',
            'short_content':
                'some short content 5, some short content 5, some short content 5, some short content 5',
            'very_short_content': 'some short content 5',
            'image_filename': 'article.png'
        }
    ]


def sim_get_latest_magazine(*args, **kwargs):
    return {"filename": "latest_magazine.pdf"}


def sim_get_books(*args, **kwargs):
    return [
        {
            'title': 'First book',
            'author': 'An author',
            'description': 'The next big thing',
            'price': '5.00',
            'image_filename': 'alchemist.jpeg'
        }
    ]
