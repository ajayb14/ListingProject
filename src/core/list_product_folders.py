
# Returns each product folder in the parent folder along with the images inside it
def list_product_folders(service, parent_folder_id):
    try:
        print("Listing product folders from Unprocessed folder")
        # We need to find the folders first, then get the images from inside each folder
        folder_query = f"'{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"

        # Get all product folders (raw data)
        folder_results = service.files().list(
            q=folder_query,
            orderBy="name",
            fields="files(id, name)"
        ).execute()

        # Extract the list of product folders from the results (Just the folders)
        # If no folders found, this will be an empty list
        product_folders = folder_results.get('files', [])
        print("Found product folders:", len(product_folders))

        folders = []

        for product_folder in product_folders:
            folder_id = product_folder['id']
            folder_name = product_folder['name']

            # Find the images inside this specific product folder
            # Change 'image/' if the files you upload are a different type
            image_query = f"'{folder_id}' in parents and mimeType contains 'image/'"

            image_results = service.files().list(
                q=image_query,
                orderBy="name",
                fields="files(id, name, mimeType)"
            ).execute()

            images = image_results.get('files', [])
            print("Images found in", folder_name, ":", len(images))

            folders.append({
                'id': folder_id,
                'name': folder_name,
                'images': images
            })

        return folders
    except Exception as e:
        print("Error in list_product_folders:", e)
        return []
