from fastapi import FastAPI, HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import app.models as pm
import logging
import sys
import uvicorn
import app.app_logic as app_logic
import urllib.parse as urlparse


logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

app = FastAPI()
# dpcnaflfhdkdeijjglelioklbghepbig
origins = [
    "chrome-extension://dpcnaflfhdkdeijjglelioklbghepbig",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex="chrome-extension://*",  # for development
    # allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"Message": "Welcome to the Summarizer Service"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logging.error(request)
    logging.error(exc)
    return PlainTextResponse(str(request), status_code=400)


@app.post("/bookmark", response_model=pm.Bookmark, status_code=201)
async def create_bookmark(url: pm.URL):
    """ file_name = f'../data/icog_pages/{page.clean_url}.json'
    with open(file_name, "w") as fp:
        json.dump(page.dict(), fp)
 """
    logging.info(f"Icognition bookmark endpoint called on {url.url}")

    page = app_logic.create_page(url.url)

    if page is None:
        raise HTTPException(
            status_code=204, detail="The webpage doesn't have article and paragraph elements")
    logging.info(f"Page created for {page.clean_url}")
    bookmark = app_logic.generate_bookmark(page)
    logging.info(f"Bookmark created for {bookmark.url}")
    return bookmark


@app.get("/bookmark", response_model=pm.Bookmark, status_code=200)
async def get_bookmark(url: str):
    url = urlparse.unquote(url)
    bookmark = app_logic.get_bookmark_by_url(url)

    if bookmark is None:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    logging.info(f"Icognition return bookmark {bookmark.id}")
    return bookmark


@app.get("/document/{id}", response_model=pm.Document)
async def get_document(id: int, response_model=pm.Document, status_code=200):
    logging.info(f"Icognition document endpoint called on {id}")
    document = app_logic.get_document_by_id(id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    keyphrases = app_logic.get_keyphrases_by_document_id(document.id)
    document.keyphrases = keyphrases
    return document


@app.get("/document/{id}/keyphrases", response_model=List[pm.Keyphrase])
async def get_document_keyphrases(id: int):
    logging.info(
        f"Icognition document keyphrases endpoint called on document {id}")

    keyphrases = app_logic.get_keyphrases_by_document_id(id)
    return keyphrases


@app.delete("/document/{id}/cascade", status_code=204)
async def delete_document(id: int) -> None:
    logging.info(f"Icognition delete document endpoint called on {id}")
    app_logic.delete_document_and_associate_records(id)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8889)
