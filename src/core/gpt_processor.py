import base64
import json

from openai import OpenAI

from .config import OPENAI_API_KEY, OPENAI_MODEL

# Soft limits: results that break them are still returned, with a warning attached
MAX_TITLE_LENGTH = 140
TARGET_TAG_COUNT = 13
# Every extra photo costs tokens
MAX_IMAGES = 5


class ListingGenerationError(Exception):
    """Raised when a listing could not be generated, carrying a reason worth showing a user."""


# Shared so the API and this module word the cap the same way
def too_many_images_warning(total):
    return f"Folder has {total} images, only the first {MAX_IMAGES} were analyzed"


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


def build_prompt(product_info, image_count):
    # Without this, several photos of one painting get described as several separate works
    if image_count > 1:
        subject = f"""The {image_count} attached photos are all of the SAME single painting, taken from
different angles or showing different details. Describe one artwork, not several, and use the extra
views to be more specific about texture, framing, and color."""
    else:
        subject = "The attached photo is of the painting being listed."

    return f"""
You are an expert marketing specialist who creates compelling, search-optimized listings for original artwork and prints.

{subject}

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
Base every answer on the actual photos, not on generic assumptions.
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


# Generate listing content from one or more photos of the same painting.
# images is a list of (bytes, mime_type) pairs; extra views make the description more specific.
def generate_listing_content(images, product_folder_name):
    usable = [(data, mime_type) for data, mime_type in images if data]
    if not usable:
        raise ListingGenerationError("No image data to analyze")

    warnings = []
    if len(usable) > MAX_IMAGES:
        warnings.append(too_many_images_warning(len(usable)))
        usable = usable[:MAX_IMAGES]

    product_info = extract_product_info(product_folder_name)

    content = [{"type": "text", "text": build_prompt(product_info, len(usable))}]
    for data, mime_type in usable:
        encoded_image = base64.b64encode(data).decode('utf-8')
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{encoded_image}"}
        })

    print("Calling", OPENAI_MODEL, "with", len(usable), "image(s) for listing content")
    try:
        response = get_client().chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": content}],
            max_tokens=1200,
            temperature=0.7
        )
    except Exception as e:
        raise ListingGenerationError(f"OpenAI request failed: {e}") from e

    try:
        data = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError as e:
        raise ListingGenerationError("Model did not return valid JSON") from e

    listing, response_warnings = normalize_listing(data)
    listing.update(product_info)
    listing['warnings'] = warnings + response_warnings
    listing['images_analyzed'] = len(usable)
    listing['model'] = OPENAI_MODEL
    if response.usage is not None:
        listing['usage'] = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens
        }

    print("Listing content generated with", len(listing['warnings']), "warnings")
    return listing


if __name__ == "__main__":
    import mimetypes
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m src.core.gpt_processor <Title_Type_Size_Price> <image_path>...")
        sys.exit(1)

    folder_name, image_paths = sys.argv[1], sys.argv[2:]

    images = []
    for image_path in image_paths:
        with open(image_path, 'rb') as f:
            images.append((f.read(), mimetypes.guess_type(image_path)[0] or 'image/jpeg'))

    try:
        result = generate_listing_content(images, folder_name)
    except ListingGenerationError as error:
        print("Failed:", error)
        sys.exit(1)

    print(json.dumps(result, indent=2))
