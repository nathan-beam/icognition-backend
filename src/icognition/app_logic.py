import json
import datetime
import sys
import logging
import torch
from db_util import Bookmark, Document, Keyphrase, ItemVector
from icog_util import Page
from transformer_text_summarizer import Summarizer
from keyphrase_extractor import KeyphraseExtraction
from pgvector.sqlalchemy import Vector
from sqlalchemy import select, create_engine, Integer, String, func
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer, util


logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

engine = create_engine('postgresql+psycopg2://app:2214@localhost/icognition')

summarizer = Summarizer()
keyphrase_extractor = KeyphraseExtraction()

stantance_model_name = "paraphrase-MiniLM-L6-v2"
device = "cuda:0" if torch.cuda.is_available() else "cpu"
sentence_transformer = SentenceTransformer(stantance_model_name, device=device)


def find_wikidata_id(kp: Keyphrase, session: Session):
    vec_query = sentence_transformer.encode(
        kp.context, show_progress_bar=False)
    items = session.query(ItemVector).order_by(
        ItemVector.text_vec.cosine_distance(vec_query)).limit(2).all()

    for item in items:
        distance = util.cos_sim(item.text_vec, vec_query)
        print('------- Context ------')
        print(f"word: {kp.word}. context: {kp.context}")
        print(item.text)
        print(distance)

    vec_query = sentence_transformer.encode(
        kp.word, show_progress_bar=False)
    items = session.query(ItemVector).order_by(
        ItemVector.text_vec.cosine_distance(vec_query)).limit(2).all()

    for item in items:
        distance = util.cos_sim(item.text_vec, vec_query)
        print('------ Word -------')
        print(f"word: {kp.word}")
        print(item.text)
        print(distance)


def create_bookmark(page: Page) -> Bookmark:

    session = Session(engine)

    # Check if document exists, retrieve the bookmark and keyphrases and return
    # if exists. Else, create the document, bookmark and keyphrase.
    # TODO: Bookmark need to be associate with user
    doc = session.scalar(select(Document).where(
        Document.url == page.clean_url))
    if doc:
        bookmark = session.scalar(
            select(Bookmark).where(Bookmark.document_id == doc.id))
        keyphrases = session.scalars(
            select(Keyphrase).where(Keyphrase.document_id == doc.id))
        logging.info('Document already exists')

        # If bookmark and keyphrase exist return the bookmark
        if bookmark and len(keyphrases) > 0:
            return bookmark

    doc = Document()
    doc.title = page.title
    doc.url = page.clean_url

    paragraphs = [v for k, v in page.paragraphs.items()]
    doc.summary_generated = summarizer(
        paragraphs, summary_length='first_chunk')[0]

    session.add(doc)
    session.commit()

    # Create bookmark
    # Create boomark if not exists
    if session.scalar(select(Bookmark).where(Bookmark.url == page.clean_url)):
        logging.info('Bookmark already exists')
        # return None

    bookmark = Bookmark()
    bookmark.url = page.clean_url
    bookmark.title = page.title
    bookmark.update_at = datetime.datetime.now()
    bookmark.document_id = doc.id

    session.add(bookmark)
    session.commit()

    logging.info(
        f'Bookmark and document created. Document id {doc.id}. Bookmark id {bookmark.id}')

    keyphrases = [Keyphrase(**kp)
                  for kp in keyphrase_extractor(page.full_text)]

    for k in keyphrases:
        k.document_id = doc.id

    session.add_all(keyphrases)
    session.commit()
    logging.info(
        f"Added {len(keyphrases)} keyphrases to database for document {doc.url}")

    session.close()
    return bookmark


if __name__ == '__main__':
    path_file = '/home/eboraks/Projects/icognition_backend/data/icog_pages/bergum.medium.com%2Ffour-mistakes-when-introducing-embeddings-and-vector-search-d39478a568c5.json'
    with open(path_file, 'r') as f:
        jpage = json.load(f)
        page = Page(**jpage)
        create_bookmark(page)
