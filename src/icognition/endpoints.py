from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from icog_util import Page
from db_util import Bookmark, Document
import logging
import sys
import uvicorn
import json

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
async def bookmark(page: Page):
    file_name = f'../data/icog_pages/{page.clean_url}.json'
    with open(file_name, "w") as fp:
        json.dump(page.dict(), fp)

    logging.info(f"Icognition bookmark endpoint called on {Page.url}")

    sentences = list(page.paragraphs.values())
    chunks = concatenate_sentences_to_chunks(sentences)

    results = []
    for chunk in chunks:
        summary = pszemraj_summarizer(chunk)
        results.append(summary[0]['summary_text'])

    page.summarized_paragraphs = results

    return page
