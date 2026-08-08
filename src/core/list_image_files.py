
# Returns a list of all images found across all product folders
def list_image_files(service, folder_id):
    try:
        print("Listing images from Unprocessed folder")
        # We need to find the folders first, then get the image from inside each folder
        folder_query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
        
        # Get all product folders (raw data)
        folder_results = service.files().list(q=folder_query, fields="files(id, name)").execute()
        
        # Extract the list of product folders from the results (Just the folders)
        # If no folders found, this will be an empty list
        product_folders = folder_results.get('files', [])
        count_product_folders = len(product_folders)
        print("Found product folders:", count_product_folders)
        
        # Create a list to store all images we find
        all_images = []
        
        # Loop through each product folder to get the image
        for product_folder in product_folders:
            # Get the unique ID and name of this product folder
            folder_id = product_folder['id']
            folder_name = product_folder['name']
            
            # Find the image inside this specific product folder
            # The query looks for files that are direct children of this product folder and are images ( change the image/ to a different file type if the file type is different)
            image_query = f"'{folder_id}' in parents and mimeType contains 'image/'"
            
            # Execute the query to get the image in this product folder
            image_results = service.files().list(q=image_query, fields="files(id, name, parents)").execute()
            
            # Extract the list of images from the results
            images = image_results.get('files', [])
            count_images = len(images)
            print("Images found in a folder:", count_images)
            
            # Get the image (If we need to get more than one image per painting, then change this to a for loop)
            if images:
                image = images[0]  # Get the single image from this folder
                # Add the product folder name to the image data 
                image['product_folder_name'] = folder_name
                # Add the product folder ID to the image data
                image['product_folder_id'] = folder_id
                # Add to list
                all_images.append(image)
        
        return all_images
    except Exception as e:
        print("Error in list_image_files:", e)
        return []