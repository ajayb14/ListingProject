import base64
import json

from openai import OpenAI

from .config import OPENAI_API_KEY, OPENAI_MODEL

# Soft limits: results that break them are still returned, with a warning attached
MAX_TITLE_LENGTH = 140
TARGET_TAG_COUNT = 13


class ListingGenerationError(Exception):
    """Raised when a listing could not be generated, carrying a reason worth showing a user."""


_client = None


# Avoid setting up a new HTTP connection pool on every button click
def get_client():
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise ListingGenerationError("OPENAI_API_KEY is missing from config.env")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


# Extract information from product folder name: <Painting title>_<Print/Original>_<Size>_<Price>
def extract_product_info(product_folder_name):
    print("Extracting product info from folder name:", product_folder_name)
    parts = product_folder_name.split('_')

    if len(parts) == 4:
        return {
            'painting_title': parts[0],
            'art_type': parts[1],
            'size': parts[2],
            'price': parts[3].lstrip('$')
        }

    print("Folder name does not match <Title>_<Type>_<Size>_<Price>. Using defaults")
    return {
        'painting_title': product_folder_name,
        'art_type': 'Original',
        'size': 'Unknown',
        'price': 'Unknown'
    }


# Kept outside the f-string below so the braces reach the model as literal JSON
RESPONSE_FORMAT_EXAMPLE = """
{
    "title": "Your optimized title here (max 140 chars)",
    "description": "Your detailed description here",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10", "tag11", "tag12", "tag13"]
}
"""


def build_prompt(product_info):
    return f"""
You are an expert marketing specialist who creates compelling, search-optimized listings for original artwork and prints.

ANALYZE THIS PAINTING AND CREATE A LISTING:

Product Information:
- Original Painting Title: "{product_info['painting_title']}"
- Art Type: {product_info['art_type']} (Print or Original)
- Size: {product_info['size']}
- Price: ${product_info['price']}

TASK: Create a search-optimized listing that will help customers find this artwork.

REQUIREMENTS:
1. TITLE (max {MAX_TITLE_LENGTH} characters): the subject/style, art type, size, and key search terms.
2. DESCRIPTION: what the painting depicts, artistic style and technique, size and material details,
   suggested rooms or occasions, care instructions, and shipping information.
3. TAGS (exactly {TARGET_TAG_COUNT}): a mix of art style, subject matter, room decor, color scheme, art type, and size.

RESPOND IN THIS EXACT JSON FORMAT:
""" + RESPONSE_FORMAT_EXAMPLE + """
Base every answer on the actual image, not on generic assumptions.
"""


# Clean up the model's response and collect anything a human should double check
def normalize_listing(data):
    warnings = []

    title = str(data.get('title') or '').strip()
    description = str(data.get('description') or '').strip()
    raw_tags = data.get('tags') or []

    missing = [name for name, value in (('title', title), ('description', description), ('tags', raw_tags)) if not value]
    if missing:
        raise ListingGenerationError("Model response was missing: " + ", ".join(missing))

    # Dedupe case-insensitively while keeping the model's ordering
    tags = []
    seen = set()
    for tag in raw_tags:
        cleaned = str(tag).strip()
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            tags.append(cleaned)

    if len(title) > MAX_TITLE_LENGTH:
        warnings.append(f"Title is {len(title)} characters, {MAX_TITLE_LENGTH} is the usual limit")
    if len(tags) != TARGET_TAG_COUNT:
        warnings.append(f"Got {len(tags)} tags instead of {TARGET_TAG_COUNT}")

    listing = {
        'title': title,
        'description': description,
        'tags': tags,
    }
    return listing, warnings


# Generate listing content from image bytes using a vision model
def generate_listing_content(image_bytes, mime_type, product_folder_name):
    if not image_bytes:
        raise ListingGenerationError("No image data to analyze")

    product_info = extract_product_info(product_folder_name)
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')

    print("Calling", OPENAI_MODEL, "for listing content")
    try:
        response = get_client().chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": build_prompt(product_info)},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{encoded_image}"}
                        }
                    ]
                }
            ],
            max_tokens=1200,
            temperature=0.7
        )
    except Exception as e:
        raise ListingGenerationError(f"OpenAI request failed: {e}") from e

    content = response.choices[0].message.content
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ListingGenerationError("Model did not return valid JSON") from e

    listing, warnings = normalize_listing(data)
    listing.update(product_info)
    listing['warnings'] = warnings
    listing['model'] = OPENAI_MODEL
    if response.usage is not None:
        listing['usage'] = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens
        }

    print("Listing content generated with", len(warnings), "warnings")
    return listing


if __name__ == "__main__":
    import mimetypes
    import sys

    if len(sys.argv) != 3:
        print("Usage: python -m src.core.gpt_processor <image_path> <Title_Type_Size_Price>")
        sys.exit(1)

    image_path, folder_name = sys.argv[1], sys.argv[2]
    guessed_mime = mimetypes.guess_type(image_path)[0] or 'image/jpeg'

    with open(image_path, 'rb') as f:
        image_data = f.read()

    try:
        result = generate_listing_content(image_data, guessed_mime, folder_name)
    except ListingGenerationError as error:
        print("Failed:", error)
        sys.exit(1)

    print(json.dumps(result, indent=2))
