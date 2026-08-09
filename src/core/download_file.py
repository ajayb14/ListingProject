import io

# This helps download large files from google drive
from googleapiclient.http import MediaIoBaseDownload


# Read a Drive file into memory, so images can go straight to the browser or OpenAI
def fetch_file_bytes(service, file_id):
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, service.files().get_media(fileId=file_id))

    done = False
    while done is False:
        status, done = downloader.next_chunk()

    return buffer.getvalue()
