from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from typing import List
import pydantic_models as pm
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


@app.post("/bookmark", response_model=pm.Bookmark)
async def bookmark(url: pm.URL):
    """ file_name = f'../data/icog_pages/{page.clean_url}.json'
    with open(file_name, "w") as fp:
        json.dump(page.dict(), fp)
 """
    logging.info(f"Icognition bookmark endpoint called on {url.url}")

    page = app_logic.create_page(url.url)
    logging.info(f"Page created for {page.clean_url}")
    bookmark = app_logic.generate_bookmark(page)
    logging.info(f"Bookmark created for {bookmark.url}")
    return bookmark


@app.get("/document/{id}", response_model=pm.Document)
async def document(id: int):
    logging.info(f"Icognition document endpoint called on {id}")
    document = app_logic.get_document_by_id(id)
    return document


@app.get("/document/{id}/keyphrases", response_model=List[pm.Keyphrase])
async def document_keyphrases(id: int):
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
