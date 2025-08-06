import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Drive API scopes (permissions). Gives me full access to google drive. It allows me to use the service functions
SCOPES = ['https://www.googleapis.com/auth/drive']

# Authenticate with Google Drive using service account.
def get_drive_service():
    
    try:
        # Get the path to the service account key file
        service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service-account-key.json')
        
        # Check if the service account key file exists
        if not os.path.exists(service_account_file):
            return None
        
        # Create credentials from the service account key file (Authentication part)
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES)
        
        # Build the Google Drive service (Service creation part)
        service = build('drive', 'v3', credentials=credentials)
        
        return service
        
    except Exception as e:
        return None
