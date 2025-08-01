import time
import os
from list_image_files import list_image_files
from download_file import download_file
from move_file_to_processed import move_file_to_processed
from drive_auth import get_drive_service
from gpt_processor import analyze_image_with_gpt, save_listing_data, print_listing_preview
from dotenv import load_dotenv

# Load variables from env file
load_dotenv()

# Get Drive Folder ID's
UNPROCESSED_FOLDER_ID = os.getenv("UNPROCESSED_FOLDER_ID")
PROCESSED_FOLDER_ID = os.getenv("PROCESSED_FOLDER_ID")

# Use polling for now, but we can use webhooks later if we want to
def drive_watcher():

    # Initialize Google Drive service
    service = get_drive_service()
    if service is None:
        print("Failed to authenticate with Google Drive. Exiting...")
        return
    print("Drive watcher started...")
    while True:
        image_files = list_image_files(service, UNPROCESSED_FOLDER_ID)

        for file in image_files:
            file_id = file['id']
            file_name = file['name']

            # Download the image to temp (or wherever we will store the downloaded images) directory
            download_file(service, file_id, file_name)

            # Call GPT and Etsy stuff here

            # Move file to processed folder
            move_file_to_processed(service, file_id)

        time.sleep(60) # Wait a minute before checking the folder for new images again