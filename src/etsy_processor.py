import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Etsy API configuration
ETSY_API_KEY = os.getenv('ETSY_API_KEY', 'placeholder_api_key')
ETSY_SHOP_ID = os.getenv('ETSY_SHOP_ID', 'placeholder_shop_id')

# Etsy API base URL
ETSY_API_BASE = "https://openapi.etsy.com/v3/application"

def create_etsy_draft_listing(listing_data, image_path, product_info):
    """
    Create a draft listing on Etsy using the generated content and product information.
    
    Args:
        listing_data: Dictionary with 'title', 'description', and 'tags'
        image_path: Path to the image file to upload
        product_info: Dictionary with 'painting_title', 'art_type', 'size', 'price'
    
    Returns:
        listing_id: The ID of the created listing, or None if failed
    """
    # Check if we have valid API credentials
    if ETSY_API_KEY == 'placeholder_api_key' or ETSY_SHOP_ID == 'placeholder_shop_id':
        return None
    
    # Step 1: Upload the image to Etsy
    image_id = upload_image_to_etsy(image_path)
    if image_id is None:
        return None
    
    # Step 2: Create the draft listing
    listing_id = create_draft_listing(listing_data, image_id, product_info)
    if listing_id is None:
        return None
    
    return listing_id

def upload_image_to_etsy(image_path):
    """
    Upload an image to Etsy and return the image ID.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        image_id: The Etsy image ID, or None if failed
    """
    # Etsy image upload endpoint
    upload_url = f"{ETSY_API_BASE}/shops/{ETSY_SHOP_ID}/listings/images"
    
    # Prepare headers
    headers = {
        'x-api-key': ETSY_API_KEY,
        'Content-Type': 'multipart/form-data'
    }
    
    # Prepare the image file
    with open(image_path, 'rb') as image_file:
        files = {'image': image_file}
        
        # Make the upload request
        response = requests.post(upload_url, headers=headers, files=files)
        
        if response.status_code == 201:
            image_data = response.json()
            return image_data['image_id']
        else:
            return None

def create_draft_listing(listing_data, image_id, product_info):
    """
    Create a draft listing on Etsy with the provided content and image.
    
    Args:
        listing_data: Dictionary with 'title', 'description', and 'tags'
        image_id: The Etsy image ID from upload
        product_info: Dictionary with product information
    
    Returns:
        listing_id: The created listing ID, or None if failed
    """
    # Etsy listing creation endpoint
    listing_url = f"{ETSY_API_BASE}/shops/{ETSY_SHOP_ID}/listings"
    
    # Prepare headers
    headers = {
        'x-api-key': ETSY_API_KEY,
        'Content-Type': 'application/json'
    }
    
    # Convert price to integer (Etsy expects price in cents)
    price_cents = int(float(product_info['price']) * 100)
    
    # Prepare listing data
    listing_payload = {
        'title': listing_data['title'],
        'description': listing_data['description'],
        'price': price_cents,
        'quantity': 1,
        'who_made': 'i_did',  # "I did" (handmade)
        'when_made': 'made_to_order',  # Made to order
        'taxonomy_id': 687,  # Art category
        'state': 'draft',  # Create as draft
        'is_supply': False,  # Not a supply
        'is_customizable': False,  # Not customizable
        'language': 'en',  # English
        'tags': listing_data['tags']
    }
    
    # Make the listing creation request
    response = requests.post(listing_url, headers=headers, json=listing_payload)
    
    if response.status_code == 201:
        listing_response = response.json()
        listing_id = listing_response['listing_id']
        
        # Add the image to the listing
        add_image_to_listing(listing_id, image_id)
        
        return listing_id
    else:
        return None

def add_image_to_listing(listing_id, image_id):
    """
    Add an uploaded image to a listing.
    
    Args:
        listing_id: The Etsy listing ID
        image_id: The Etsy image ID
    """
    # Etsy image association endpoint
    image_url = f"{ETSY_API_BASE}/listings/{listing_id}/images/{image_id}"
    
    headers = {
        'x-api-key': ETSY_API_KEY
    }
    
    # Associate the image with the listing
    response = requests.post(image_url, headers=headers)
    
    # No need to check response status as this is just adding image to existing listing

def test_etsy_connection():
    """
    Test the Etsy API connection and credentials.
    """
    if ETSY_API_KEY == 'placeholder_api_key' or ETSY_SHOP_ID == 'placeholder_shop_id':
        return False
    
    # Test endpoint - get shop info
    test_url = f"{ETSY_API_BASE}/shops/{ETSY_SHOP_ID}"
    headers = {'x-api-key': ETSY_API_KEY}
    
    response = requests.get(test_url, headers=headers)
    
    if response.status_code == 200:
        return True
    else:
        return False 