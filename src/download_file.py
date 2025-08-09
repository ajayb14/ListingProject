# This helps download large files from google drive
from googleapiclient.http import MediaIoBaseDownload
import io
import os
import shutil

# This downloads a file from google drive to the local machine
def download_file(service, file_id, file_name, product_folder_name):
    fh = None
    try:
        print("Starting download for:", file_name)
        print("Product folder name:", product_folder_name)
        
        # Create downloaded_images_etsy directory if it doesn't exist
        download_dir = "downloaded_images_etsy"
        exists_download_dir = os.path.exists(download_dir)
        if not exists_download_dir:
            os.makedirs(download_dir)
            print("Created directory:", download_dir)
        else:
            print("Using directory:", download_dir)
        
        # Clean the folder name for filesystem compatibility
        safe_folder_name = ""
        for c in product_folder_name:
            if c.isalnum() or c in (' ', '-', '_'):
                safe_folder_name = safe_folder_name + c
        safe_folder_name = safe_folder_name.rstrip()
        print("Safe folder name for the download directory:", safe_folder_name)
        
        # Create the product directory if it doesn't exist
        product_dir = os.path.join(download_dir, safe_folder_name)
        exists_product_dir = os.path.exists(product_dir)
        if not exists_product_dir:
            os.makedirs(product_dir)
            print("Created product directory:", product_dir)
        else:
            print("Using product directory:", product_dir)
        
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
        fh = None
        
        print("Download complete")
        return download_path, safe_folder_name
    except Exception as e:
        print("Error in download_file:", e)
        if fh is not None:
            try:
                fh.close()
            except Exception:
                pass
        return None, None


# Delete downloaded image files inside the product folder, but keep the directories
def cleanup_etsy_images_files(safe_folder_name):
    try:
        print("Starting cleanup for product folder")
        
        download_dir = "downloaded_images_etsy"
        product_dir = os.path.join(download_dir, safe_folder_name)
        exists_product_dir = os.path.exists(product_dir)
        if not exists_product_dir:
            print("Product directory not found")
            return
        
        entries = os.listdir(product_dir)
        for entry_name in entries:
            entry_path = os.path.join(product_dir, entry_name)
            is_file = os.path.isfile(entry_path)
            if is_file:
                os.remove(entry_path)
                print("Deleted file:", entry_path)
        
        print("Cleanup finished for:", product_dir)
    except Exception as e:
        print("Error in cleanup_etsy_images_files:", e)