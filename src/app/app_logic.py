import datetime
import sys
import logging
import torch
from app import html_parser
from app.models import Bookmark, Document, Keyphrase, WD_ItemVector, Page
from app.transformer_text_summarizer import Summarizer
from app.keyphrase_extractor import KeyphraseExtraction
from pgvector.sqlalchemy import Vector
from sqlalchemy import select, delete, create_engine, Integer, String, func
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer, util


logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

engine = create_engine('postgresql+psycopg2://app:2214@localhost/icog_db')

summarizer = Summarizer()
keyphrase_extractor = KeyphraseExtraction()

stantance_model_name = "paraphrase-MiniLM-L6-v2"
device = "cuda:0" if torch.cuda.is_available() else "cpu"
sentence_transformer = SentenceTransformer(stantance_model_name, device=device)


def find_wikidata_id(kp: Keyphrase, session: Session):
    vec_query = sentence_transformer.encode(
        kp.context, show_progress_bar=False)
    items = session.query(WD_ItemVector).order_by(
        WD_ItemVector.text_vec.cosine_distance(vec_query)).limit(2).all()

    for item in items:
        distance = util.cos_sim(item.text_vec, vec_query)
        print('------- Context ------')
        print(f"word: {kp.word}. context: {kp.context}")
        print(item.text)
        print(distance)

    vec_query = sentence_transformer.encode(
        kp.word, show_progress_bar=False)
    items = session.query(WD_ItemVector).order_by(
        WD_ItemVector.text_vec.cosine_distance(vec_query)).limit(2).all()

    for item in items:
        distance = util.cos_sim(item.text_vec, vec_query)
        print('------ Word -------')
        print(f"word: {kp.word}")
        print(item.text)
        print(distance)


def delete_document_and_associate_records(document_id) -> None:
    """
    This function deletes a document and all associated records from the database. 
    This function was create for testing purposes. 
    """
    logging.info(f"Deleting document {document_id} and associated records")
    session = Session(engine)
    session.execute(delete(Document).where(Document.id == document_id))
    session.execute(delete(Keyphrase).where(
        Keyphrase.document_id == document_id))
    session.execute(delete(Bookmark).where(
        Bookmark.document_id == document_id))
    session.commit()
    session.close()
    logging.info(f"Document {document_id} and associated records deleted")


def get_document_by_id(document_id) -> Document:
    session = Session(engine)
    doc = session.scalar(select(Document).where(
        Document.id == document_id))
    session.close()
    return doc


def get_document_by_url(url) -> Document:
    session = Session(engine)
    doc = session.scalar(select(Document).where(
        Document.url == url))
    session.close()
    return doc


def get_keyphrases_by_document_id(document_id) -> Keyphrase:
    session = Session(engine)
    keyphrases = session.scalars(select(Keyphrase).where(
        Keyphrase.document_id == document_id)).all()
    session.close()
    return keyphrases


def get_keyphrases_by_document_url(url) -> list[Keyphrase]:
    session = Session(engine)
    stmt = select(Keyphrase).join(
        Document, Keyphrase.document_id == Document.id).where(
            Document.url == url)
    keyphrases = session.scalars(stmt).all()
    session.close()
    return keyphrases


def create_page(url) -> Page:
    url = html_parser.clean_url(url)
    html = html_parser.get_webpage(url)
    paragraphs = html_parser.get_paragraphs(html)

    if (paragraphs is None):
        logging.error("No paragraphs found in webpage")
        return None

    title = html_parser.get_title(html)

    page = Page()
    page.clean_url = url
    page.paragraphs = paragraphs
    page.title = title

    return page


def generate_bookmark(page: Page) -> Bookmark:

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
        if bookmark and len(keyphrases.all()) > 0:
            session.close()
            return bookmark

    doc = Document()
    doc.title = page.title
    doc.url = page.clean_url

    doc.summary_generated = summarizer(
        page.paragraphs, summary_length='first_chunk')[0]

    session.add(doc)
    session.commit()

    # Create bookmark
    # Create boomark if not exists
    if session.scalar(select(Bookmark).where(Bookmark.url == page.clean_url)):
        logging.info('Bookmark already exists')
        # return None

    bookmark = Bookmark()
    bookmark.url = page.clean_url
    bookmark.update_at = datetime.datetime.now()
    bookmark.document_id = doc.id

    session.add(bookmark)
    session.commit()

    # Storing the bookmark and document id in variable
    # to be use to get a fresh bookmark for the funtion return
    # This is to avoid the error: DetachedInstanceError
    bookmark_id = bookmark.id
    document_id = doc.id

    logging.info(
        f'Bookmark and document created. Document id {doc.id}. Bookmark id {bookmark.id}')

    full_text = '\n'.join(page.paragraphs)
    keyphrases = [Keyphrase(**kp)
                  for kp in keyphrase_extractor(full_text)]

    for k in keyphrases:
        k.document_id = doc.id

    session.add_all(keyphrases)
    session.commit()
    logging.info(
        f"Added {len(keyphrases)} keyphrases to database for document {doc.url}")

    bookmark = session.scalar(select(Bookmark).where(
        Bookmark.id == bookmark_id, Bookmark.document_id == document_id))

    session.close()

    return bookmark


def get_bookmark_by_url(url: str) -> Bookmark:
    url = html_parser.clean_url(url)
    session = Session(engine)
    bookmark = session.scalar(select(Bookmark).where(
        Bookmark.url == url))
    session.close()
    return bookmark


if __name__ == '__main__':
    delete_document_and_associate_records(11)
