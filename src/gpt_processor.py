import os
import json
import base64
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Encode image to base64 for GPT-4 Vision API
def encode_image_to_base64(image_path):
    
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Extract information from product folder name: <Painting title>_<Print/Original>_<Size>_<Price>
def extract_product_info(product_folder_name):
    
    parts = product_folder_name.split('_')
    
    if len(parts) == 4:
        painting_title = parts[0]
        art_type = parts[1]  # Print or Original
        size = parts[2]
        price = parts[3]
        
        return {
            'painting_title': painting_title,
            'art_type': art_type,
            'size': size,
            'price': price
        }
    else:
        # if format doesn't match, use the folder name as the painting title
        return {
            'painting_title': product_folder_name,
            'art_type': 'Original',
            'size': 'Unknown',
            'price': 'Unknown'
        }

# Generate Etsy listing content using GPT-4 Vision
def generate_etsy_listing_content(image_path, product_folder_name):
    
    try:
        # Extract product information from folder name
        product_info = extract_product_info(product_folder_name)
        
        # Encode image
        base64_image = encode_image_to_base64(image_path)
        
        # Create the prompt with product information
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
{{
    "title": "Your optimized title here (max 140 chars)",
    "description": "Your detailed description here",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10", "tag11", "tag12", "tag13"]
}}

Focus on making this listing discoverable through Etsy search while accurately representing the artwork.
"""

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
        
        # Extract the response content (text)
        content = response.choices[0].message.content
        
        # Try to parse (change from text to python data) JSON response
        try:
            listing_data = json.loads(content)
            
            # Validate the response
            if 'title' in listing_data and 'description' in listing_data and 'tags' in listing_data:
                if len(listing_data['title']) <= 140 and len(listing_data['tags']) == 13:
                    # Return both listing data and product info
                    return listing_data, product_info
                else:
                    print(f"Invalid response format: title length or tag count incorrect")
                    return None, None
            else:
                print(f"Missing required fields in GPT response")
                return None, None
                
        except json.JSONDecodeError:
            print(f"Failed to parse JSON response from GPT")
            return None, None
            
    except Exception as e:
        print(f"Error generating Etsy listing content: {e}")
        return None, None 