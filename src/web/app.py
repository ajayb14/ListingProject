import json
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from googleapiclient.errors import HttpError
from pydantic import BaseModel

from ..core.config import PROJECT_ROOT, UNPROCESSED_FOLDER_ID
from ..core.download_file import fetch_file_bytes
from ..core.drive_authentication import get_drive_service
from ..core.gpt_processor import (
    MAX_IMAGES,
    ListingGenerationError,
    extract_product_info,
    generate_listing_content,
    too_many_images_warning
)
from ..core.list_product_folders import list_images_in_folder, list_product_folders
from ..core.move_folder_to_processed import move_product_folder_to_processed

app = FastAPI(title="Listing Generator")

SAVE_DIR = PROJECT_ROOT / "generated_listings"
# Angular's build output, mounted only once it exists so dev works without a build
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist" / "frontend" / "browser"


class FolderRequest(BaseModel):
    folder_id: str


# A fresh service per request: googleapiclient service objects are not thread safe
def drive():
    service = get_drive_service()
    if service is None:
        raise HTTPException(status_code=503, detail="Could not authenticate with Google Drive. Check the server logs.")
    return service


@app.exception_handler(HttpError)
def handle_drive_error(request, exc):
    return JSONResponse(status_code=502, content={'detail': f"Google Drive error: {exc.reason}"})


@app.exception_handler(ListingGenerationError)
def handle_listing_error(request, exc):
    return JSONResponse(status_code=502, content={'detail': str(exc)})


# Folders without images can't produce a listing, so they never reach the picker
@app.get("/api/folders")
def get_folders():
    folders = list_product_folders(drive(), UNPROCESSED_FOLDER_ID)
    return [
        {**folder, 'product_info': extract_product_info(folder['name'])}
        for folder in folders
        if folder['images']
    ]


@app.get("/api/image/{file_id}")
def get_image(file_id: str, download: bool = False):
    service = drive()
    metadata = service.files().get(fileId=file_id, fields='name, mimeType').execute()
    image_bytes = fetch_file_bytes(service, file_id)

    headers = {}
    if download:
        headers['Content-Disposition'] = f'attachment; filename="{metadata["name"]}"'

    return Response(content=image_bytes, media_type=metadata['mimeType'], headers=headers)


@app.post("/api/generate")
def generate(request: FolderRequest):
    service = drive()
    folder = service.files().get(fileId=request.folder_id, fields='id, name').execute()

    images = list_images_in_folder(service, folder['id'])
    if not images:
        raise HTTPException(status_code=400, detail=f"No images found in {folder['name']}")

    # Every photo of the painting goes to the model, so extra angles improve the description.
    # Sliced before downloading so a folder full of strays does not pull megabytes we discard.
    downloaded = [
        (fetch_file_bytes(service, image['id']), image['mimeType'])
        for image in images[:MAX_IMAGES]
    ]
    listing = generate_listing_content(downloaded, folder['name'])

    if len(images) > MAX_IMAGES:
        listing['warnings'].append(too_many_images_warning(len(images)))

    result = {
        'folder_id': folder['id'],
        'folder_name': folder['name'],
        'images': images,
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        **listing
    }
    result['saved_to'] = str(save_listing(result).relative_to(PROJECT_ROOT))
    return result


@app.post("/api/mark-done")
def mark_done(request: FolderRequest):
    move_product_folder_to_processed(drive(), request.folder_id)
    return {'folder_id': request.folder_id, 'status': 'moved to Processed'}


# Keep a copy on disk so a closed tab doesn't mean paying for another generation
def save_listing(result):
    SAVE_DIR.mkdir(exist_ok=True)

    safe_name = ''.join(c for c in result['folder_name'] if c.isalnum() or c in ' -_').strip()
    path = SAVE_DIR / f"{safe_name or result['folder_id']}.json"
    path.write_text(json.dumps(result, indent=2))

    print("Saved listing to", path)
    return path


# Mounted last so it never shadows the API routes above
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
