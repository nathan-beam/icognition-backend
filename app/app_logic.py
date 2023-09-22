import datetime
import sys
import logging
from app import html_parser
from app.models import Bookmark, Keyphrase, WD_ItemVector, Page, Document
from app.hf_api_caller import HfAPICaller, LlamaTemplates
from app.spacy_ner_caller import NerCaller
from sqlalchemy import select, delete, create_engine, and_, Integer, String, func
from sqlalchemy.orm import Session
from dotenv import dotenv_values


logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s - %(message)s",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)

config = dotenv_values(".env")

engine = create_engine(config["LOCAL_PSQL"])


hf_caller = HfAPICaller()
ner_caller = NerCaller()


def delete_bookmark_and_associate_records(bookmark_id) -> None:
    """
    This function deletes a bookmark and all associated records from the database.
    This function was create for testing purposes.
    """
    logging.info(f"Deleting bookmark {bookmark_id} and associated records")
    with Session(engine) as session:
        session.execute(delete(Document).where(Document.bookmark_id == bookmark_id))
        session.execute(delete(Bookmark).where(Bookmark.id == bookmark_id))
        session.commit()
        logging.info(f"Bookmark {bookmark_id} and associated records deleted")


def delete_all_of_users_records(user_id: int) -> None:
    """Delete all of the records for a user. This function was create for testing

    Args:
        user_id int
    """
    bookmarks = get_bookmark_by_user_id(user_id)
    for bookmark in bookmarks:
        delete_bookmark_and_associate_records(bookmark.document_id)


def get_document_by_bookmark_id(bookmark_id) -> Document:
    session = Session(engine)
    doc = session.scalar(select(Document).where(Document.bookmark_id == bookmark_id))
    session.close()
    return doc


def get_document_by_id(document_id) -> Document:
    session = Session(engine)
    doc = session.scalar(select(Document).where(Document.id == document_id))
    session.close()
    return doc


def get_document_by_url(url) -> Bookmark:
    session = Session(engine)
    doc = session.scalar(select(Bookmark).where(Bookmark.url == url))
    session.close()
    return doc


def get_keyphrases_by_document_id(document_id) -> Keyphrase:
    session = Session(engine)
    keyphrases = session.scalars(
        select(Keyphrase).where(Keyphrase.document_id == document_id)
    ).all()
    session.close()
    return keyphrases


def get_keyphrases_by_document_url(url) -> list[Keyphrase]:
    session = Session(engine)
    stmt = (
        select(Keyphrase)
        .join(Bookmark, Keyphrase.document_id == Bookmark.id)
        .where(Bookmark.url == url)
    )
    keyphrases = session.scalars(stmt).all()
    session.close()
    return keyphrases


def create_page(url: str) -> Page:
    page = html_parser.create_page(url)
    if page == None:
        logging.info(f"Page not found for url {url}")
        return None

    return page


def generate_document(page: Page, bookmark_id: int):
    """
    Function that takes pages and return a document with the generated summary,
    bullet points and entities generate by LLM
    """
    templates = LlamaTemplates()
    doc = Document()
    doc.title = page.title
    doc.url = page.clean_url
    doc.bookmark_id = bookmark_id

    concepts_query = templates.concepts(page.full_text)
    bp_query = templates.bullet_points(page.full_text)
    en_query = templates.people_org_places(page.full_text)

    found_entities_raw = hf_caller.generate(en_query)
    concepts = hf_caller.generate(concepts_query)
    summary_bullet_points = hf_caller.generate(bp_query)

    ner_entities = ner_caller(page.full_text)

    if found_entities_raw:
        doc.llama2_entities_raw = found_entities_raw
    else:
        logging.info(f"No entities found for url {page.clean_url}")

    if concepts:
        doc.concepts_generated = concepts
    else:
        logging.info(f"No summary generated for url {page.clean_url}")
    if summary_bullet_points:
        doc.summary_bullet_points = summary_bullet_points
    else:
        logging.info(f"No bullet points generated for url {page.clean_url}  ")

    if ner_entities:
        doc.spacy_entities_json = ner_entities
    else:
        logging.info(f"No NER entities were found")

    doc.update_at = datetime.datetime.now()

    with Session(engine) as session:
        session.add(doc)
        session.commit()


def generate_bookmark(page: Page) -> Bookmark:
    session = Session(engine)

    # Check if document exists, retrieve the bookmark and keyphrases and return
    # if exists. Else, create the document, bookmark and keyphrase.
    user_id = config["DUMMY_USER"]

    bookmark = session.scalar(
        select(Bookmark).where(
            and_(Bookmark.url == page.clean_url, Bookmark.user_id == user_id)
        )
    )

    if bookmark:
        logging.info(f"Bookmark from url {page.clean_url} already exists")
        session.close()
        return bookmark

    bookmark = Bookmark()
    bookmark.url = page.clean_url
    bookmark.update_at = datetime.datetime.now()

    session.add(bookmark)
    # session.add(doc)
    session.commit()

    logging.info(f"Bookmark was created with id {bookmark.id}")

    session.close()

    return bookmark


def get_bookmark_by_user_id(user_id: int) -> list[Bookmark]:
    session = Session(engine)
    bookmarks = session.scalars(
        select(Bookmark).where(Bookmark.user_id == user_id)
    ).all()
    session.close()
    return bookmarks


def get_bookmark_by_url(url: str) -> Bookmark:
    url = html_parser.clean_url(url)
    session = Session(engine)
    bookmark = session.scalar(select(Bookmark).where(Bookmark.url == url))
    session.close()
    return bookmark


def get_bookmark_document(id: int) -> Document:
    session = Session(engine)
    doc = session.scalar(select(Document).where(Document.bookmark_id == id))
    session.close()
    return doc


def get_bookmark_by_id(id: int) -> Bookmark:
    session = Session(engine)
    bookmark = session.scalar(select(Bookmark).where(Bookmark.id == id))
    session.close()
    return bookmark
