# This Lists the images in a folder
def list_image_files(service, folder_id):
    drive_file_query = f"'{folder_id}' in parents and mimeType contains 'image/'"
    results = service.files().list(q=drive_file_query, fields="files(id, name)").execute()
    return results.get('files', [])