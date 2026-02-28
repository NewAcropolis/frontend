import base64
from datetime import datetime, timedelta
from flask import current_app
from google.cloud import storage

from na_common.dates import get_nice_event_dates as common_get_nice_event_dates


def get_nice_event_dates(events, future_dates_only=False):
    for event in events:
        event['original_event_dates'] = event['event_dates']
        if future_dates_only:
            event['event_dates'] = get_future_event_dates(event['event_dates'])
        event = get_nice_event_date(event)
    return events


def get_nice_event_date(event, set_timemarkers=True):
    event_date_count = len(event['original_event_dates']) if 'original_event_dates' in event else 0
    event['formatted_event_datetimes'] = common_get_nice_event_dates(event['event_dates'],
                                                                     show_time=event['event_type'] != 'Competition')
    event['dates'] = get_event_dates(event['event_dates'])
    event['date_offset'] = event_date_count - len(event['dates'])

    event_date = event["event_dates"][0]
    _datetime = datetime.strptime(event_date["event_datetime"], '%Y-%m-%d %H:%M')
    if event['event_type'] == 'Introductory Course':
        event['event_monthyear'] = _datetime.strftime('%B %Y')

    event_date['event_time'] = _datetime.strftime('%H:%M')
    if not event.get('event_time'):
        event['event_time'] = event_date['event_time']
    elif set_timemarkers:
        if _datetime.minute > 0:
            time = _datetime.strftime('%-I:%M %p')
        else:
            time = _datetime.strftime('%-I %p')
        event['event_time'] = time
    if not event.get('end_time'):
        event['end_time'] = event_date["end_time"]
        if event_date["end_time"] and event_date["end_time"] != "00:00":
            _end_time = datetime.strptime(event_date["end_time"], '%H:%M')
            if _end_time.minute > 0:
                time = _end_time.strftime('%-I:%M %p')
            else:
                time = _end_time.strftime('%-I %p')
            event['formatted_event_datetimes'] += " to " + time

    return event


def get_future_event_dates(event_dates):
    future_dates = []
    for event_date in event_dates:
        _datetime = datetime.strptime(event_date["event_datetime"], '%Y-%m-%d %H:%M')
        if _datetime >= datetime.today():
            future_dates.append(event_date)

    return future_dates


def get_event_dates(event_dates):
    dates = []
    for event_date in event_dates:
        _datetime = datetime.strptime(event_date["event_datetime"], '%Y-%m-%d %H:%M')
        dates.append(_datetime.strftime('%Y-%m-%d'))

    return dates


def size_from_b64(b64string):
    # adjust file size as base64 increases the size by about 30%
    return (float(len(b64string) * 3) / 4 - b64string.count('=', -2)) * 0.77


def purge_old_tmp_files(days=7):
    storage_client = storage.Client()

    purged = []
    blobs = storage_client.list_blobs(f"{current_app.config.get('STORAGE')}", prefix="tmp")
    for blob in blobs:
        expiry_date = blob.updated.replace(tzinfo=None) + timedelta(days=1)
        is_expired = expiry_date < datetime.now()
        if is_expired:
            blob.reload()
            generation_match_precondition = blob.generation

            try:
                blob.delete(if_generation_match=generation_match_precondition)
                purged.append(
                    {
                        "name": blob.name,
                        "updated": blob.updated,
                        "expiry": expiry_date,
                        "expired": is_expired
                    }
                )
            except Exception:
                current_app.logger.warn(f"#{blob.name} not deleted")

    return purged


def upload_blob_from_base64string(
    src_filename, destination_blob_name, base64data, content_type='image/png'
):
    data_len = len(base64data)
    current_app.logger.info('Uploading {} file {} uploaded to {}'.format(
        sizeof_fmt(data_len),
        src_filename,
        destination_blob_name))

    storage_client = storage.Client()
    bucket = storage_client.bucket(current_app.config.get('STORAGE'))

    blob = bucket.blob(destination_blob_name)

    binary = base64.b64decode(base64data)

    blob.upload_from_string(binary, content_type=content_type)
    blob.make_public()

    data_len = len(binary)
    current_app.logger.info('Uploaded {} file {} uploaded to {}'.format(
        sizeof_fmt(data_len),
        src_filename,
        destination_blob_name))


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Gi', suffix)
