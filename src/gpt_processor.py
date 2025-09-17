import os
import json
import base64
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

# Set up OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Encode image to base64 for GPT-4 Vision API
def encode_image_to_base64(image_path):
    try:
        print("Encoding image to base64")
        with open(image_path, "rb") as image_file:
            data = image_file.read()
        encoded = base64.b64encode(data)
        text = encoded.decode('utf-8')
        print("Image encoded successfully")
        return text
    except Exception as e:
        print("Error in encode_image_to_base64:", e)
        return None

# Extract information from product folder name: <Painting title>_<Print/Original>_<Size>_<Price>
def extract_product_info(product_folder_name):
    try:
        print("Extracting product info from folder name:", product_folder_name)
        parts = product_folder_name.split('_')
        
        if len(parts) == 4:
            painting_title = parts[0]
            art_type = parts[1]
            size = parts[2]
            price = parts[3]
            info = {
                'painting_title': painting_title,
                'art_type': art_type,
                'size': size,
                'price': price
            }
            print("Extracted product info")
            return info
        else:
            # if format doesn't match, use the folder name as the painting title
            info = {
                'painting_title': product_folder_name,
                'art_type': 'Original',
                'size': 'Unknown',
                'price': 'Unknown'
            }
            print("Folder name format unknown. Using defaults")
            return info
    except Exception as e:
        print("Error in extract_product_info:", e)
        fallback = {
            'painting_title': product_folder_name,
            'art_type': 'Original',
            'size': 'Unknown',
            'price': 'Unknown'
        }
        return fallback

# Generate Etsy listing content using GPT-4 Vision
def generate_etsy_listing_content(image_path, product_folder_name):
    try:
        print("Generating Etsy listing content with GPT")
        # Extract product information from folder name
        product_info = extract_product_info(product_folder_name)
        
        # Encode image to base64 for GPT-4 Vision API
        base64_image = encode_image_to_base64(image_path)
        if base64_image is None:
            print("Failed to encode image. Cannot call GPT")
            return None, None
        
        prompt = f"""
You are an expert Etsy marketing specialist who creates compelling, search-optimized listings for original artwork and prints.

ANALYZE THIS PAINTING AND CREATE AN ETSY LISTING:

Product Information:
- Original Painting Title: "{product_info['painting_title']}"
- Art Type: {product_info['art_type']} (Print or Original)
- Size: {product_info['size']}
- Price: ${product_info['price']}

TASK: Create a search-optimized Etsy listing that will help customers find this artwork.

REQUIREMENTS:
1. TITLE (max 140 characters): Create a compelling, searchable title that includes:
   - The painting's subject/style
   - Art type (Print/Original)
   - Size information
   - Key search terms people would use

2. DESCRIPTION: Write a detailed, engaging description that includes:
   - What the painting depicts
   - Artistic style and technique
   - Size and material details
   - Perfect for (room/occasion suggestions)
   - Care instructions
   - Shipping information

3. TAGS (exactly 13 tags): Include relevant search terms like:
   - Art style (abstract, landscape, portrait, etc.)
   - Subject matter (nature, flowers, animals, etc.)
   - Room decor (living room, bedroom, office, etc.)
   - Color scheme (blue, green, neutral, etc.)
   - Art type (print, original, wall art, etc.)
   - Size (small, medium, large, etc.)

RESPOND IN THIS EXACT JSON FORMAT:
{
    "title": "Your optimized title here (max 140 chars)",
    "description": "Your detailed description here",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10", "tag11", "tag12", "tag13"]
}

Focus on making this listing discoverable through Etsy search while accurately representing the artwork.
"""
        
        print("Calling GPT-4 Vision API")
        # Call GPT-4 Vision API
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.7
        )
        print("Received response from GPT")
        # Extract the response content (text)
        content = response.choices[0].message.content
        print("Parsing GPT response JSON")
        

        # Validate the response
        try:
            listing_data = json.loads(content)
            has_title = 'title' in listing_data
            has_description = 'description' in listing_data
            has_tags = 'tags' in listing_data
            if has_title and has_description and has_tags:
                title_ok = len(listing_data['title']) <= 140
                tags_ok = len(listing_data['tags']) == 13
                if title_ok and tags_ok:
                    print("Validated GPT response")
                    # Return both listing data and product info
                    return listing_data, product_info
                else:
                    print("Invalid response format: title length or tag count incorrect")
                    return None, None
            else:
                print("Missing required fields in GPT response")
                return None, None
        except json.JSONDecodeError:
            print("Failed to parse JSON response from GPT")
            return None, None
        
    except Exception as e:
        print("Error generating Etsy listing content:", e)
        return None, None

# Test the GPT integration
def test_gpt_integration():
    
    print("=== Testing GPT-4 Vision Integration ===")
    
    # Check if OpenAI API key is set
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("OPENAI_API_KEY not found in environment variables")
        return False
    
    print("OpenAI API key found")
    
    # Test image path - you'll need to provide a real image path
    test_image_path = "test_image.jpg"  # Change this to your test image path
    test_product_folder_name = "Sunset_Landscape_Original_16x20_150"
    
    # Check if test image exists
    if not os.path.exists(test_image_path):
        print(f"❌ Test image not found: {test_image_path}")
        print("Please provide a valid image path for testing")
        return False
    
    print(f"Test image found: {test_image_path}")
    print(f"Test product folder name: {test_product_folder_name}")
    
    try:
        print("Testing GPT-4 Vision integration...")
        listing_data, product_info = generate_etsy_listing_content(test_image_path, test_product_folder_name)
        
        if listing_data is not None and product_info is not None:
            print("GPT integration test successful!")
            print("\n--- Generated Listing Data ---")
            print(f"Title: {listing_data['title']}")
            print(f"Title length: {len(listing_data['title'])} characters")
            print(f"Description preview: {listing_data['description'][:100]}...")
            print(f"Number of tags: {len(listing_data['tags'])}")
            print(f"Tags: {', '.join(listing_data['tags'])}")
            print("\n--- Product Info ---")
            print(f"Painting title: {product_info['painting_title']}")
            print(f"Art type: {product_info['art_type']}")
            print(f"Size: {product_info['size']}")
            print(f"Price: ${product_info['price']}")
            return True
        else:
            print("GPT integration test failed")
            return False
            
    except Exception as e:
        print(f"GPT integration test error: {e}")
        return False

if __name__ == "__main__":
    test_gpt_integration()