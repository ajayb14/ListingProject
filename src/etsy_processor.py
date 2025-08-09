import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Etsy API configuration
ETSY_API_KEY = os.getenv('ETSY_API_KEY')
ETSY_SHOP_ID = os.getenv('ETSY_SHOP_ID')

# Etsy API base URL (Makes it easier to build API URLs)
ETSY_API_BASE = "https://openapi.etsy.com/v3/application"

# Create a draft listing on Etsy using the generated content and product information.
def create_etsy_draft_listing(listing_data, image_path, product_info):
    try:
        print("Starting Etsy draft listing creation")
        if ETSY_API_KEY == None or ETSY_SHOP_ID == None:
            print("Missing ETSY_API_KEY or ETSY_SHOP_ID")
            return None
        
        image_id = upload_image_to_etsy(image_path)
        if image_id is None:
            print("Image upload failed")
            return None
        
        listing_id = create_draft_listing(listing_data, image_id, product_info)
        if listing_id is None:
            print("Draft listing creation failed")
            return None
        
        print("Draft listing created")
        return listing_id
    except Exception as e:
        print("Error in create_etsy_draft_listing:", e)
        return None

# Upload an image to Etsy and return the image ID.
def upload_image_to_etsy(image_path):
    try:
        print("Uploading image to Etsy")
        upload_url = f"{ETSY_API_BASE}/shops/{ETSY_SHOP_ID}/listings/images"
        
        headers = {
            'x-api-key': ETSY_API_KEY,
            'Content-Type': 'multipart/form-data'
        }
        
        with open(image_path, 'rb') as image_file:
            files = {'image': image_file}
            response = requests.post(upload_url, headers=headers, files=files)
            print("Upload response status:", response.status_code)
            if response.status_code == 201:
                image_data = response.json()
                image_id = image_data.get('image_id')
                if image_id is not None:
                    print("Image uploaded")
                    return image_id
                else:
                    print("No image ID in response")
                    return None
            else:
                print("Upload failed")
                return None
    except Exception as e:
        print("Error in upload_image_to_etsy:", e)
        return None

# Create a draft listing on Etsy with the content and image
def create_draft_listing(listing_data, image_id, product_info):
    try:
        print("Creating draft listing")
        listing_url = f"{ETSY_API_BASE}/shops/{ETSY_SHOP_ID}/listings"
        
        headers = {
            'x-api-key': ETSY_API_KEY,
            'Content-Type': 'application/json'
        }
        
        price_cents = int(float(product_info['price']) * 100)
        
        listing_payload = {
            'title': listing_data['title'],
            'description': listing_data['description'],
            'price': price_cents,
            'quantity': 1,
            'who_made': 'i_did',
            'when_made': 'made_to_order',
            'taxonomy_id': 687,
            'state': 'draft',
            'is_supply': False,
            'is_customizable': False,
            'language': 'en',
            'tags': listing_data['tags']
        }
        
        response = requests.post(listing_url, headers=headers, json=listing_payload)
        print("Listing creation response status:", response.status_code)
        if response.status_code == 201:
            listing_response = response.json()
            listing_id = listing_response.get('listing_id')
            print("Draft listing created")
            add_image_to_listing(listing_id, image_id)
            print("Associated uploaded image with the listing")
            return listing_id
        else:
            print("Draft listing creation failed")
            return None
    except Exception as e:
        print("Error in create_draft_listing:", e)
        return None

# Add an uploaded image to a listing.
def add_image_to_listing(listing_id, image_id):
    try:
        print("Associating image with listing")
        image_url = f"{ETSY_API_BASE}/listings/{listing_id}/images/{image_id}"
        
        headers = {
            'x-api-key': ETSY_API_KEY
        }
        
        response = requests.post(image_url, headers=headers)
        print("Image association response status:", response.status_code)
    except Exception as e:
        print("Error in add_image_to_listing:", e)