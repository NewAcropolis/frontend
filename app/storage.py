import base64

from google.cloud import storage


def upload_blob(destination_blob_name, base64data):
    """Uploads a file to the bucket."""
    bucket_name = "dev-event-images"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    binary = base64.b64decode(base64data)

    blob.upload_from_string(binary, content_type='image/png')
    blob.make_public()

    binary_len = len(binary)
    current_app.logger.info('Uploaded {} file {} uploaded to {}'.format(
        sizeof_fmt(binary_len),
        src_filename,
        destination_blob_name))

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )