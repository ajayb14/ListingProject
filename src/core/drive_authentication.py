import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

# Google Drive API scopes (permissions). Gives me full access to google drive. It allows me to use the service functions
SCOPES = ['https://www.googleapis.com/auth/drive']

# Authenticate with Google Drive using service account.
def get_drive_service():
    try:
        print("Starting Google Drive authentication")
        
        # Get the path to the service account key file
        service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service-account-key.json')
        
        # Check if the service account key file exists
        exists_key_file = os.path.exists(service_account_file)
        if not exists_key_file:
            print("Service account key file not found")
            return None
        
        # Create credentials from the service account key file (Authentication part)
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES)
        print("Credentials created")
        
        # Build the Google Drive service (Service creation part)
        service = build('drive', 'v3', credentials=credentials)
        print("Google Drive service created")
        
        return service
        
    except Exception as e:
        print("Error in get_drive_service:", e)
        return None

# Test the drive authentication
def test_drive_connection():
    print("Testing Google Drive Authentication")
    
    service = get_drive_service()
    if service is None:
        print("Drive authentication failed")
        return False
    
    try:
        # Test listing files to verify connection works
        print("Testing file listing...")
        service.files().list(pageSize=1).execute()
        print("Successfully listed files from Google Drive")
        print("Drive authentication test passed")
        return True
        
    except Exception as e:
        print(f"Drive connection test failed: {e}")
        return False

if __name__ == "__main__":
    test_drive_connection()
