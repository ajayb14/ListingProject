from dotenv import load_dotenv
import os

# Load environment variables from env file
load_dotenv()

# Folder ID for destination (processed folder)
PROCESSED_FOLDER_ID = os.getenv("PROCESSED_FOLDER_ID")

def move_product_folder_to_processed(service, product_folder_id):
    """
    Move an entire product folder from Unprocessed to Processed.
    """
    # Get the current parents of the product folder
    folder = service.files().get(fileId=product_folder_id, fields='parents').execute()
    
    # Get the parents list
    parents_list = folder.get('parents')
    
    # Get the single parent
    previous_parents = parents_list[0]
    
    # Move the entire product folder to the processed folder
    service.files().update(
        fileId=product_folder_id,
        addParents=PROCESSED_FOLDER_ID,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()
