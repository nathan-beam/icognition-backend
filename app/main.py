from fastapi import FastAPI, HTTPException, BackgroundTasks, status, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from app.models import (
    Bookmark,
    Document,
    PagePayload,
    DocumentDisplay,
    HTTPError,
    SearchPayload,
)
import logging
import sys, re, time
import uvicorn
import re
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
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Welcome to Icognition API"}


@app.get("/ping", status_code=200)
async def ping():
    try:
        bm = app_logic.test_db_connection()
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Database connection failed")

    return {"Message": "Service is up and running"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logging.error(request)
    logging.error(exc)
    return PlainTextResponse(str(request), status_code=400)


@app.post(
    "/bookmark",
    responses={
        400: {
            "model": HTTPError,
            "description": "Reporting back errors",
        },
        201: {"model": Bookmark, "description": "Bookmark created successfully"},
    },
)
async def create_bookmark(
    payload: PagePayload, background_tasks: BackgroundTasks, response: Response
):

    logging.info(f"Icognition bookmark endpoint called on {payload.url}")

    if payload.user_id == None:
        logging.warn(f"User ID not provided for {payload.url}")
        raise HTTPException(
            status_code=400,
            detail="User ID not provided for the bookmark",
        )

    # Check if payload.url is not the root URL of a website
    if re.match(r"^https?://[^/]+/$", payload.url):
        logging.warn(f"Invalid URL provided: {payload.url}")
        raise HTTPException(
            status_code=400,
            detail="I am sorry, I can't analyze home pages",
        )

    page = app_logic.create_page(payload)

    if page is None:
        logging.warn(f"Page object not created for {payload.url}")
        raise HTTPException(
            status_code=400,
            detail="Hmm, I wasn't able to find information on this page. I sent a message to our engineers",
        )

    ## Check in bookmark already exists
    bookmark = app_logic.get_bookmark_by_url(page.clean_url)
    if bookmark is not None:
        logging.info(f"Bookmark already exists for {page.clean_url}")
        response.status_code = status.HTTP_201_CREATED
        return bookmark
    else:
        logging.info(f"Page object created for {page.clean_url}")
        bookmark = app_logic.create_bookmark(page, payload.user_id)
        logging.info(f"Bookmark created for {bookmark.url}")
        background_tasks.add_task(generate_document, bookmark.document_id)
        response.status_code = status.HTTP_201_CREATED
        return bookmark


@app.post(
    "/document/regenerate",
    response_model=Bookmark,
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_regenerate_document(
    old_doc: Document, background_tasks: BackgroundTasks
):
    """
    This method create document using a bookmark id and a URL.
    Because create_bookmark also generate document, this method is use to re-generate
    the a document. Because it can take time to generate a document, this method
    kickoff the generate and return 202
    """
    logging.info(f"Regenrate Document ID {old_doc.id}")
    # Generate LLM content in a background process

    # Reason for returning bookmark is because the document will changed after the regeneration,
    # and the bookmark will be used to get the new document
    new_doc = app_logic.clone_document(old_doc)
    background_tasks.add_task(regenerate_document, new_doc)
    bookmark = app_logic.reassociate_bookmark_with_document(old_doc.id, new_doc.id)

    if bookmark is None:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    return bookmark


## Background task to generate summaries from LLM
async def generate_document(document_id):
    document = app_logic.get_document_by_id(document_id)

    if document.status in ["Pending", "Done", "Failure"]:
        logging.info(f"Background task for document ID: {document_id}")
        document = await app_logic.extract_info_from_doc(document)
        logging.info(f"Background task for document ID: {document_id} completed")


## Background task to regenerate summaries from LLM if not already exists
async def regenerate_document(doc: Document):

    if doc.status in ["Pending", "Done", "Failure"]:

        new_doc = await app_logic.extract_info_from_doc(doc)
        if new_doc:
            logging.info(f"Background task for document ID: {new_doc.id} completed")
        else:
            logging.error(
                f"Background document regenaring for document ID: {doc.id} failed"
            )


@app.get("/bookmark/user/{user_id}", response_model=List[Bookmark], status_code=200)
async def get_bookmarks_by_user_id(user_id: str):
    bookmarks = app_logic.get_bookmarks_by_user_id(user_id)

    if bookmarks is None:
        raise HTTPException(status_code=404, detail="Bookmarks not found")

    logging.info(f"Icognition return {len(bookmarks)} bookmarks")
    return bookmarks


@app.get(
    "/documents_plus/user/{user_id}",
    response_model=List[DocumentDisplay],
    status_code=200,
)
async def get_documents_plus_by_user_id(user_id: str):
    bookmarks = app_logic.get_bookmarks_by_user_id(user_id)

    if bookmarks is None:
        raise HTTPException(status_code=404, detail="Bookmarks not found")

    results = []
    for bookmark in bookmarks:
        document = app_logic.get_document_by_id(bookmark.document_id)
        entities = app_logic.get_entities_by_document_id(document.id)

        display = DocumentDisplay.from_orm(document, entities=entities)

        results.append(display)

    logging.info(f"Icognition return {len(results)} documents_plus")
    return results


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


@app.get("/document_plus/{bookmark_id}", response_model=DocumentDisplay)
async def get_document_plus(bookmark_id: int, response: Response, background_tasks: BackgroundTasks):
    """get document with entities and concepts"""

    logging.info(f"Document plus -> endpoint called on bookmark {bookmark_id}")
    document = app_logic.get_document_by_bookmark_id(bookmark_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # If document is still in processing, let the client know
    if document.status in ["Processing", "Pending"]:
        response.status_code = status.HTTP_206_PARTIAL_CONTENT
        logging.info(
            f"Document plus -> endpoint called on document status {document.status}"
        )
        return DocumentDisplay.from_orm(document)
    elif document.status == "Done":
        entities = app_logic.get_entities_by_document_id(document.id)

        response.status_code = status.HTTP_200_OK
        logging.info(
            f"Document plus -> endpoint called on document status {document.status}"
        )

        # Generate embeddings for the document
        background_tasks.add_task(generate_embedding)

        return DocumentDisplay.from_orm(document, entities=entities)
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return DocumentDisplay.from_orm(document)


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


@app.get("/entities/{user_id}", response_model=List, status_code=200)
async def post_entities_tree(user_id: str):
    logging.info(f"Post entities tree")
    entities = app_logic.get_entities_by_user_id(user_id)
    return entities


@app.get("/entities_tree/{user_id}", response_model=List, status_code=200)
async def post_entities_tree(user_id: str):
    logging.info(f"Post entities tree")
    entities = app_logic.get_entities_tree_by_user_id(user_id)
    return entities


@app.post("/search", response_model=List[DocumentDisplay], status_code=200)
async def search_documents(search_payload: SearchPayload):
    logging.info(f"Search documents")
    
    if(search_payload.query == None):
        documents = app_logic.search_documents(search_payload.user_id, search_payload.query)
    else:
        documents = app_logic.search_embeddings(search_payload.user_id, search_payload.query)

    return documents


@app.get("/generate_embedding", status_code=200)
async def generate_embedding():
    try:
        await app_logic.generate_documents_embeddings()
        return {"Message": "Embedding generation completed"}
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Embedding generation failed")
