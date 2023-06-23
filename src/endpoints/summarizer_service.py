from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from transformers.pipelines import AggregationStrategy
from transformers import (
    TokenClassificationPipeline,
    AutoModelForTokenClassification,
    AutoTokenizer,
    pipeline,
)
from sentence_transformers import SentenceTransformer, util
import numpy as np
import lancedb

from typing import Union
import torch
import logging
import sys
import uvicorn
import json

logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

app = FastAPI()

embeddings = SentenceTransformer('all-MiniLM-L6-v2')


# Define keyphrase extraction pipeline
class KeyphraseExtractionPipeline(TokenClassificationPipeline):
    def __init__(self, model, *args, **kwargs):
        super().__init__(
            model=AutoModelForTokenClassification.from_pretrained(model),
            tokenizer=AutoTokenizer.from_pretrained(model),
            *args,
            **kwargs
        )

    def postprocess(self, all_outputs):
        mid_results = super().postprocess(
            all_outputs=all_outputs,
            aggregation_strategy=AggregationStrategy.FIRST,
        )
        strings = set()
        results = []
        for kp in mid_results:
            if kp.get("word") not in strings:
                strings.add(kp.get("word"))
                results.append(kp)

        return results


# pipelines initation
device = "cuda:0" if torch.cuda.is_available() else "cpu"
# bart_summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
pegasus_summarizer = pipeline(
    "summarization", model="google/pegasus-cnn_dailymail")
pszemraj_summarizer = pipeline(
    "summarization", model="pszemraj/led-base-book-summary")
# Load pipeline
model_name = "ml6team/keyphrase-extraction-distilbert-inspec"
keyphrase_extractor = KeyphraseExtractionPipeline(model=model_name)

st_model = SentenceTransformer('all-MiniLM-L6-v2')


def concatenate_sentences_to_chunks(sentences):
    """
    Iterates over a list of sentences and concatenates them to 500-word chunks.

    Args:
      sentences: A list of sentences.

    Returns:
      A list of 500-word chunks.
    """

    chunks = []
    current_chunk = ''
    for sentence in sentences:
        current_chunk += sentence.replace('\n', ' ')
        if len(current_chunk.split(' ')) >= 1000:
            chunks.append(current_chunk)
            current_chunk = ''

    chunks.append(current_chunk)
    return chunks


@app.get("/")
async def root():
    return {"Message": "Welcome to the Summarizer Service"}


class textBlob(BaseModel):
    source: Union[str, None] = None
    text: str


class Page(BaseModel):
    url: Union[str, None] = None
    title: Union[str, None] = None
    clean_url: Union[str, None] = None
    paragraphs: Union[dict, None] = None
    summarized_paragraphs: Union[list, None] = None
    key_concepts: Union[list, None] = None
    full_text: Union[str, None] = None


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logging.error(request)
    logging.error(exc)
    return PlainTextResponse(str(request), status_code=400)


@app.post("/one_sentance")
async def one_sentance(text: textBlob):
    logging.info("One sentance action")
    return pegasus_summarizer(text.text)


@app.post("/page_processing")
async def page_processing(page: Page):
    file_name = f'../data/icog_pages/{page.clean_url}.json'
    with open(file_name, "w") as fp:
        json.dump(page.dict(), fp)

    logging.info("icognition summary mathod start")

    sentences = list(page.paragraphs.values())
    chunks = concatenate_sentences_to_chunks(sentences)

    results = []
    for chunk in chunks:
        summary = pszemraj_summarizer(chunk)
        results.append(summary[0]['summary_text'])

    page.summarized_paragraphs = results

    return page


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8889)
