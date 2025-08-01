# This creates an object to interact with the google drive API
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

# Load environment variables from env file
load_dotenv()

# Folder ID for destination (processed folder)
PROCESSED_FOLDER_ID = os.getenv("PROCESSED_FOLDER_ID")

# Moves file from input folder to processed folder
def move_file_to_processed(service, file_id):
    # Get the current parents of the file
    file = service.files().get(fileId=file_id, fields='parents').execute()
    # Google drive api needs a string and not a list of parents
    previous_parents = ",".join(file.get('parents'))

    # Move the file to the processed folder by updating its parents with the processed folder ID
    service.files().update(
        fileId=file_id,
        addParents=PROCESSED_FOLDER_ID,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()
    print(f"File {file_id} moved to processed folder.")
