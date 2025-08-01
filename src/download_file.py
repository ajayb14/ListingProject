# This helps download large files from google drive
from googleapiclient.http import MediaIoBaseDownload
import io
import os


# This downloads a file from google drive to the local machine
def download_file(service, file_id, file_name):
    file_request = service.files().get_media(fileID=file_id)
    fh = io.FileIO(f"temp/{file_name}", 'wb')
    downloader = MediaIoBaseDownload(fh, file_request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}% complete.")