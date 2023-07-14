from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from icog_util import Page
from db_util import Bookmark, Document, Keyphrase
import logging
import sys
import uvicorn
import json
import app_logic

logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

app = FastAPI()


@app.get("/")
async def root():
    return {"Message": "Welcome to the Summarizer Service"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logging.error(request)
    logging.error(exc)
    return PlainTextResponse(str(request), status_code=400)


@app.post("/bookmark")
async def bookmark(page: Page) -> Bookmark:
    file_name = f'../data/icog_pages/{page.clean_url}.json'
    with open(file_name, "w") as fp:
        json.dump(page.dict(), fp)

    logging.info(f"Icognition bookmark endpoint called on {Page.url}")

    bookmark = app_logic.create_bookmark(page)
    return bookmark


@app.post("/document")
async def document(id: int) -> Document:
    logging.info(f"Icognition document endpoint called on {id}")
    document = app_logic.get_document(id)
    return document


@app.post("/keyphrase")
async def keyphrase(id: int) -> Keyphrase:
    logging.info(f"Icognition keyphrase endpoint called on {id}")
    keyphrases = app_logic.get_document_keyphrases(id)
    return keyphrases
