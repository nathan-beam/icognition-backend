from fastapi import FastAPI, HTTPException, BackgroundTasks, status, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from app.models import Bookmark, Document, PagePayload, DocumentPlus
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
origins = [
    "chrome-extension://oeilkphkfimekfadiflbljknbhfmppej",
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
async def create_bookmark(payload: PagePayload, background_tasks: BackgroundTasks):
    """file_name = f'../data/icog_pages/{page.clean_url}.json'
    with open(file_name, "w") as fp:
        json.dump(page.dict(), fp)
    """
    logging.info(f"Icognition bookmark endpoint called on {payload.url}")

    page = app_logic.create_page(payload)

    if page is None:
        logging.warn(f"Page object not created for {payload.url}")
        raise HTTPException(
            status_code=204,
            detail="The webpage doesn't have article and paragraph elements",
        )

    ## Check in bookmark already exists
    bookmark = app_logic.get_bookmark_by_url(page.clean_url)
    if bookmark is not None:
        logging.info(f"Bookmark already exists for {page.clean_url}")
        return bookmark
    else:
        logging.info(f"Page object created for {page.clean_url}")
        bookmark = app_logic.create_bookmark(page)
        logging.info(f"Bookmark created for {bookmark.url}")
        background_tasks.add_task(generate_document, bookmark.document_id)
        return bookmark


@app.post("/document", response_model=Document, status_code=status.HTTP_202_ACCEPTED)
async def regenerate_document(doc: Document, background_tasks: BackgroundTasks):
    """
    This method create document using a bookmark id and a URL.
    Because create_bookmark also generate document, this method is use to re-generate
    the a document. Because it can take time to generate a document, this method
    kickoff the generate and return 202
    """
    logging.info(f"Regenrate Document ID {doc.id}")

    # Generate LLM content in a background process
    background_tasks.add_task(generate_document, doc.id)
    return doc


## Background task to generate summaries from LLM if not already exists
async def generate_document(document_id):
    doc = app_logic.get_document_by_id(document_id)

    if doc.status in ["Pending", "Done", "Failure"]:
        logging.info(f"Background task for generating document ID {document_id}")
        app_logic.extract_info_from_doc(doc)


@app.get("/bookmark/user/{user_id}", response_model=List[Bookmark], status_code=200)
async def get_bookmarks_by_user_id(user_id: int = 777):
    bookmarks = app_logic.get_bookmarks_by_user_id(user_id)

    if bookmarks is None:
        raise HTTPException(status_code=404, detail="Bookmarks not found")

    logging.info(f"Icognition return {len(bookmarks)} bookmarks")
    return bookmarks


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


@app.get("/document_plus/{id}")
async def get_document_plus(id: int, response: Response):
    """get document with entities and concepts"""

    logging.info(f"Icognition document plus endpoint called on {id}")
    document = app_logic.get_document_by_id(id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # If document is still in processing, let the client know
    if document.status == "Processing":
        response.status_code = status.HTTP_206_PARTIAL_CONTENT
        return None
    elif document.status == "Done":
        concepts = app_logic.get_concepts_by_document_id(id)
        entities = app_logic.get_entities_by_document_id(id)

        response.status_code = status.HTTP_200_OK
        return DocumentPlus(document=document, concepts=concepts, entities=entities)
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"document": document}


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


@app.delete("/document/{id}", status_code=204)
async def delete_document(id: int) -> None:
    logging.info(f"Delete document and associated records for id: {id}")
    app_logic.delete_document_and_associate_records(id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8889)
