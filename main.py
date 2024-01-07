from fastapi import FastAPI, HTTPException, BackgroundTasks, status, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from app.models import Bookmark, Document, DocRequest, URL
import logging
import sys
import uvicorn
import app.app_logic as app_logic
import urllib.parse as urlparse


logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s - %(message)s",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI()
# dpcnaflfhdkdeijjglelioklbghepbig
origins = [
    "chrome-extension://dpcnaflfhdkdeijjglelioklbghepbig",
    "chrome-extension://*",
    "*://localhost:*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # allow_origin_regex="*",  # "chrome-extension://*",  # for development
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


@app.post("/bookmark", response_model=Bookmark, status_code=201)
async def create_bookmark(url: URL, background_tasks: BackgroundTasks):
    """file_name = f'../data/icog_pages/{page.clean_url}.json'
    with open(file_name, "w") as fp:
        json.dump(page.dict(), fp)
    """
    logging.info(f"Icognition bookmark endpoint called on {url.url}")

    page = app_logic.create_page(url.url)

    if page is None:
        logging.warn(f"Page object not created for {url.url}")
        raise HTTPException(
            status_code=204,
            detail="The webpage doesn't have article and paragraph elements",
        )

    logging.info(f"Page object created for {page.clean_url}")
    bookmark = app_logic.create_bookmark(page)
    logging.info(f"Bookmark created for {bookmark.url}")
    background_tasks.add_task(generate_document, bookmark.document_id)
    return bookmark


@app.post("/document", status_code=status.HTTP_202_ACCEPTED)
async def regenerate_document(req: DocRequest, background_tasks: BackgroundTasks):
    """
    This method create document using a bookmark id and a URL.
    Because create_bookmark also generate document, this method is use to re-generate
    the a document. Because it can take time to generate a document, this method
    kickoff the generate and return 202
    """
    logging.info(f"Regenrate Document ID {req.document_id} and url {req.url}")

    # Generate LLM content in a background process
    background_tasks.add_task(generate_document, req.document_id)


## Background task to generate summaries from LLM if not already exists
async def generate_document(document_id):
    doc = app_logic.get_document_by_id(document_id)

    if doc.status in ["Pending", "Done", "Failure"]:
        logging.info(f"Background task for generating document ID {document_id}")
        app_logic.extract_info_from_doc(doc)


@app.get("/bookmark", response_model=Bookmark, status_code=200)
async def get_bookmark_by_url(url: str):
    bookmark = app_logic.get_bookmark_by_url(url)

    if bookmark is None:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    logging.info(f"Icognition return bookmark {bookmark.id}")
    return bookmark


@app.get("/bookmark/{id}/document")
async def get_bookmark_document(id: int, response: Response):
    logging.info(f"Icognition bookmark document endpoint called on {id}")
    document = app_logic.get_document_by_bookmark_id(id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # If document is still in processing, let the client know
    if document.status == "Processing":
        response.status_code = status.HTTP_206_PARTIAL_CONTENT
        return document
    else:
        response.status_code = status.HTTP_200_OK
        return document


@app.get("/document/{id}")
async def get_document(id: int, response: Response):
    logging.info(f"Icognition document endpoint called on {id}")
    document = app_logic.get_document_by_id(id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # If document is still in processing, let the client know
    if document.status == "Processing":
        response.status_code = status.HTTP_206_PARTIAL_CONTENT
        return document
    else:
        response.status_code = status.HTTP_200_OK
        return document


@app.get("/document/{id}/concepts")
async def get_concepts(id: int, response: Response):
    logging.info(f"Icognition document concepts endpoint called on {id}")
    concepts = app_logic.get_concepts_by_document_id(id)

    if concepts is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=404, detail="Concepts not found")
    else:
        response.status_code = status.HTTP_200_OK
        return concepts


@app.get("/document/{id}/entities")
async def get_entities(id: int, response: Response):
    logging.info(f"Icognition document entities endpoint called on {id}")
    entities = app_logic.get_entities_by_document_id(id)

    if entities is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=404, detail="Entities not found")
    else:
        response.status_code = status.HTTP_200_OK
        return entities


@app.delete("/bookmark/{id}/document", status_code=204)
async def delete_bookmark(id: int) -> None:
    logging.info(f"Delete bookmark and associated records for id: {id}")
    app_logic.delete_bookmark_and_associate_records(id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8889)
