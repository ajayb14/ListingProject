# This helps download large files from google drive
from googleapiclient.http import MediaIoBaseDownload
import io
import os
import shutil

# This downloads a file from google drive to the local machine
def download_file(service, file_id, file_name, product_folder_name):
    # Create downloaded_images_etsy directory if it doesn't exist
    download_dir = "downloaded_images_etsy"
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    # Clean the folder name for filesystem compatibility (the names of the folders "<Painting title>_<Print/Original>_<Size>_<Price>" are not safe for filesystems)
    safe_folder_name = ""
    # Loop and check each character
    for c in product_folder_name:
        # If the character is part of the alphabet, a number, or one of the things below, they are safe characters
        if c.isalnum() or c in (' ', '-', '_'):
            safe_folder_name = safe_folder_name + c
    # Remove any trailing whitespace (just to look better)
    safe_folder_name = safe_folder_name.rstrip()
    
    # Create the product directory
    product_dir = os.path.join(download_dir, safe_folder_name)
    os.makedirs(product_dir)
    
    # Create the download path
    download_path = os.path.join(product_dir, file_name)
    
    # Get the file from Google Drive
    file_request = service.files().get_media(fileId=file_id)
    
    # Open file for writing 
    fh = io.FileIO(download_path, 'wb')
    
    # Create downloader
    downloader = MediaIoBaseDownload(fh, file_request)
    done = False
    
    # Download the file
    while done is False:
        status, done = downloader.next_chunk()
    
    # Close the file
    fh.close()
    
    return download_path, safe_folder_name


# Delete downloaded images and folders from downloaded_images_etsy directory after we have processed it
def cleanup_etsy_images_files(safe_folder_name):
    
    download_dir = "downloaded_images_etsy"
    
    # Delete the specific product folder
    product_dir = os.path.join(download_dir, safe_folder_name)
    if os.path.exists(product_dir):
        shutil.rmtree(product_dir)