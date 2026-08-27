# ListingAIAgent

Pick a painting folder from Google Drive, click a button, and get back everything you need to write
the listing by hand: a search-optimized title, a full description, 13 tags, and the price, size, and
art type parsed from the folder name.

The app hands you the text and the images; you create the listing yourself.

## How it works

```
Drive "Unprocessed" folder          FastAPI (port 8000)            Angular (port 4200)
  Painting_Original_8x10_150/  -->  GET  /api/folders        -->   folder dropdown
    photo.jpg                       GET  /api/image/{id}     -->   image previews
                                    POST /api/generate       -->   title / description / tags
                                    POST /api/mark-done      -->   moves folder to "Processed"
```

The image never touches your disk on the way to OpenAI. It is read from Drive into memory, sent to
the model, and every generated listing is also saved to `generated_listings/` so a closed tab does
not mean paying for another generation.

## Requirements

- Python 3.13 (a virtualenv at `listing-agent-env/` is expected)
- Node.js and the Angular CLI, for the frontend
- A Google Cloud service account with the Drive API enabled
- An OpenAI API key with credit available

## Setup

1. Install the Python dependencies:

   ```bash
   listing-agent-env/bin/pip install -r requirements.txt
   ```

2. Install the frontend dependencies:

   ```bash
   cd frontend && npm install
   ```

3. Put your service account key at `service-account-key.json` in the repo root, and share both Drive
   folders with the service account's email address (Viewer is not enough, it needs to move folders).

4. Create `config.env` in the repo root:

   ```
   OPENAI_API_KEY = sk-...
   UNPROCESSED_FOLDER_ID = "drive folder id"
   PROCESSED_FOLDER_ID = "drive folder id"
   GOOGLE_SERVICE_ACCOUNT_FILE = "service-account-key.json"
   ```

   Optionally add `OPENAI_MODEL = gpt-4o-mini` to trade quality for cost. The default is `gpt-4o`.

5. Confirm Drive authentication works:

   ```bash
   listing-agent-env/bin/python -m src.core.drive_authentication
   ```

## Drive folder layout

Inside your Unprocessed folder, one folder per painting, named:

```
<Title>_<Print|Original>_<Size>_<Price>
```

For example `Rolling Hills_Original_8x10_100`. Put the photos of the painting inside that folder. A
name that does not split into exactly four underscore-separated parts still works, but the whole name
is treated as the title and the other fields fall back to defaults.

Multiple photos of the same painting are welcome: up to five are sent to the model together, and the
extra angles make the description more specific about texture, framing, and color.

Folders with no images are hidden from the dropdown, since they cannot produce a listing.

## Running it

Two terminals during development:

```bash
# backend
listing-agent-env/bin/uvicorn src.web.app:app --reload --port 8000

# frontend
cd frontend && npm start
```

Then open http://localhost:4200. The Angular dev server proxies `/api` to port 8000 (see
`frontend/proxy.conf.json`), so no CORS configuration is needed.

FastAPI also serves interactive API docs at http://localhost:8000/docs, which is a quick way to call
the endpoints without the UI.

To run it as a single server instead, build the frontend first and FastAPI will serve it:

```bash
cd frontend && npm run build
listing-agent-env/bin/uvicorn src.web.app:app --port 8000
```

Then everything lives at http://localhost:8000.

## Layout

```
src/core/     Drive access, folder-name parsing, and the OpenAI call
src/web/      FastAPI app exposing the four endpoints
frontend/     Angular UI (one component, typed service, signals)
```

`src/core/config.py` is the single place that reads `config.env`, and it resolves every path from the
repo root, so commands work from any directory.

## Known limitations

- Generated listings are saved locally to `generated_listings/`, not back into the Drive folder. A
  service account has no Drive storage quota of its own, so creating files in a folder that is merely
  shared with it fails with `storageQuotaExceeded`. Writing the listing into Drive would require
  authenticating as a real user via OAuth.
- At most five images per folder are sent to the model. Extra photos of the same painting improve the
  description, but each one adds to the cost, so the cap keeps a stray upload from being expensive.
  Folders holding more than five say so in the UI and in the result's warnings.
