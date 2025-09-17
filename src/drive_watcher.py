import time
import os
from list_image_files import list_image_files
from download_file import download_file, cleanup_etsy_images_files
from move_folder_to_processed import move_product_folder_to_processed
from drive_authentication import get_drive_service
from gpt_processor import generate_etsy_listing_content
from etsy_processor import create_etsy_draft_listing
from dotenv import load_dotenv

# Load variables from env file
load_dotenv('config.env')

# Get Drive Folder ID's
UNPROCESSED_FOLDER_ID = os.getenv("UNPROCESSED_FOLDER_ID")
PROCESSED_FOLDER_ID = os.getenv("PROCESSED_FOLDER_ID")

# Single-run watcher: process one image if available, then exit
def drive_watcher():
    print("Starting drive watcher")
    # Initialize Google Drive service 
    service = get_drive_service()
    if service is None:
        print("Failed to initialize Google Drive service")
        return
    
    try:
        print("Checking for images in Unprocessed folder")
        image_files = list_image_files(service, UNPROCESSED_FOLDER_ID)
        
        if image_files:
            print("Images found. Processing first image")
            file = image_files[0]
            product_folder_id = file.get('product_folder_id')
            product_folder_name = file.get('product_folder_name')
            
            if product_folder_id is not None and product_folder_name is not None:
                file_id = file['id']
                file_name = file['name']
                
                download_path, safe_folder_name = download_file(service, file_id, file_name, product_folder_name)
                
                if download_path is not None:
                    print("Image downloaded locally")
                    listing_data, product_info = generate_etsy_listing_content(download_path, product_folder_name)
                    
                    if listing_data is not None and product_info is not None:
                        print("Received listing content from GPT")
                        listing_id = create_etsy_draft_listing(listing_data, download_path, product_info)
                        
                        if listing_id is not None:
                            print("Created Etsy draft listing")
                            move_product_folder_to_processed(service, product_folder_id)
                            print("Moved product folder to Processed")
                            cleanup_etsy_images_files(safe_folder_name)
                            print("Cleaned up local downloaded images")
                            return
                        else:
                            print("Failed to create Etsy draft listing")
                            cleanup_etsy_images_files(safe_folder_name)
                            print("Cleaned up local downloaded images")
                            return
                    else:
                        print("Failed to generate listing content from GPT")
                        cleanup_etsy_images_files(safe_folder_name)
                        print("Cleaned up local downloaded images")
                        return
                else:
                    print("Failed to download image")
                    return
            else:
                print("Missing product folder information. Exiting")
                return
        else:
            print("No images found")
            return
    except Exception as e:
        print("Error in drive_watcher:", e)
        return

if __name__ == "__main__":
    drive_watcher()