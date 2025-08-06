import time
import os
from list_image_files import list_image_files
from download_file import download_file, cleanup_etsy_images_files
from move_folder_to_processed import move_product_folder_to_processed
from dotenv import load_dotenv

# Load variables from env file
load_dotenv()

# Get Drive Folder ID's
UNPROCESSED_FOLDER_ID = os.getenv("UNPROCESSED_FOLDER_ID")
PROCESSED_FOLDER_ID = os.getenv("PROCESSED_FOLDER_ID")

# Use polling for now, but we can use webhooks later if we want to
def drive_watcher():
    # Initialize Google Drive service here
    service = None
    if service is None:
        return
    
    while True:
        # Get list of images from all product folders
        image_files = list_image_files(service, UNPROCESSED_FOLDER_ID)
        
        # Do one image at a time
        if image_files:
            # Get the image and folderinformation
            file = image_files[0]
            product_folder_id = file.get('product_folder_id')
            product_folder_name = file.get('product_folder_name')
            
            # Check if we have valid folder information
            if product_folder_id is not None and product_folder_name is not None:
                file_id = file['id']
                file_name = file['name']
                
                # Download the image to product subdirectory
                download_path, safe_folder_name = download_file(service, file_id, file_name, product_folder_name)
                
                # Check if download was successful
                if download_path is not None:
                    # Call GPT and Etsy stuff here
                    
                    # Move the product folder to processed
                    move_product_folder_to_processed(service, product_folder_id)
                    
                    # Delete the downloaded images from the downloaded_images_etsy folder
                    cleanup_etsy_images_files(safe_folder_name)
        
        time.sleep(60) # Wait a minute before checking the folder for new images again

if __name__ == "__main__":
    drive_watcher()