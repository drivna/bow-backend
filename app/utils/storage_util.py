from google.cloud import storage
from datetime import timedelta
from io import BytesIO

service_account_key_path = "app/utils/bucket.json"
bucket_name = "bow_pdf"


def upload_pdf_bytes(file_bytes, destination_blob_name):
    """
    Uploads PDF bytes to GCS.
    """
    storage_client = storage.Client.from_service_account_json(service_account_key_path)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    file_obj = BytesIO(file_bytes)
    blob.upload_from_file(file_obj, content_type="application/pdf")

    print(f"Uploaded to gs://{bucket_name}/{destination_blob_name}")

    return


def get_signed_url(blob_name, expiration_days=1):
    storage_client = storage.Client.from_service_account_json(service_account_key_path)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version="v4", expiration=timedelta(days=expiration_days), method="GET"
    )
    return url
