import datetime
import sys
import logging
from app import html_parser
from app.models import Bookmark, Entity, Concept, Page, Document, PagePayload
from app.together_api_client import InclusiveTemplate, TogetherMixtralClient
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

engine = create_engine(config["LOCAL_PSQL"], client_encoding="utf8")

mixtralClient = TogetherMixtralClient()
inclusiveTemplate = InclusiveTemplate()


def delete_bookmark_and_associate_records(bookmark_id) -> None:
    """
    This function deletes a bookmark and all associated records from the database.
    This function was create for testing purposes.
    """
    doc = get_document_by_bookmark_id(bookmark_id)

    logging.info(f"Deleting bookmark {bookmark_id} and associated records")
    with Session(engine) as session:
        session.execute(delete(Document).where(Document.id == doc.id))
        session.execute(delete(Bookmark).where(Bookmark.id == bookmark_id))
        session.execute(delete(Entity).where(Entity.document_id == doc.id))
        session.execute(delete(Concept).where(Concept.document_id == doc.id))
        session.commit()
        logging.info(f"Bookmark {bookmark_id} and associated records deleted")


def delete_document_and_associate_records(document_id) -> None:
    """
    This function deletes a document and all associated records from the database.
    This function was create for testing purposes.
    """
    logging.info(f"Deleting document {document_id} and associated records")
    with Session(engine) as session:
        session.execute(delete(Document).where(Document.id == document_id))
        session.execute(delete(Entity).where(Entity.document_id == document_id))
        session.execute(delete(Concept).where(Concept.document_id == document_id))
        session.commit()
        logging.info(f"Document {document_id} and associated records deleted")


def delete_all_of_users_records(user_id: int) -> None:
    """Delete all of the records for a user. This function was create for testing

    Args:
        user_id int
    """
    bookmarks = get_bookmarks_by_user_id(user_id)
    for bookmark in bookmarks:
        delete_bookmark_and_associate_records(bookmark.id)


def get_document_by_bookmark_id(bookmark_id) -> Document:
    session = Session(engine)
    doc = session.scalar(
        select(Document)
        .join(Bookmark, Bookmark.document_id == Document.id)
        .where(Bookmark.id == bookmark_id)
    )
    session.close()
    return doc


def get_document_by_id(document_id) -> Document:
    session = Session(engine)
    doc = session.scalar(select(Document).where(Document.id == document_id))
    session.close()
    return doc


def get_document_by_url(url) -> Document:
    session = Session(engine)
    doc = session.scalar(select(Document).where(Document.url == url))
    session.close()
    return doc


def get_documents_ids() -> list[int]:
    session = Session(engine)
    docs_ids = session.scalars(select(Document.id))
    session.close()
    return docs_ids


def get_entities_by_document_id(document_id) -> Entity:
    session = Session(engine)
    entities = session.scalars(
        select(Entity).where(Entity.document_id == document_id)
    ).all()
    session.close()
    return entities


def get_concepts_by_document_id(document_id) -> Concept:
    session = Session(engine)
    concepts = session.scalars(
        select(Concept).where(Concept.document_id == document_id)
    ).all()
    session.close()
    return concepts


def create_page(payload: PagePayload) -> Page:
    page = html_parser.create_page(payload)
    if page == None:
        logging.info(f"Page not found for url {payload.url}")
        return None

    return page


def create_document(page: Page):
    session = Session(engine)
    doc = session.scalar(select(Document).where(Document.url == page.clean_url))

    ## If Document isn't already exist, create it
    if doc:
        session.close()
        return doc

    doc = Document()
    doc.title = page.title
    doc.url = page.clean_url
    doc.original_text = page.full_text
    session.add(doc)
    session.commit()
    session.refresh(doc)
    session.close()

    return doc


def update_document(doc: Document, related_objects: list[list] = None):
    with Session(engine) as session:
        session.add(doc)

        if related_objects:
            logging.info(f"Adding related objects to document {doc.id}")
            for related_object in related_objects:
                session.add_all(related_object)
        session.commit()
        session.refresh(doc)
        return doc


def extract_info_from_doc(doc: Document):
    """
    Function that takes pages and return a document with the generated summary,
    bullet points and entities generate by LLM
    """

    doc.status = "Processing"
    update_document(doc)

    try:
        logging.info(f"Generating summary for document {doc.id}")
        response = mixtralClient.generate(doc.original_text, inclusiveTemplate)
        logging.info(f"Response from LLM {response}")
        summary_obj = inclusiveTemplate.handleResponse(response)
        logging.info(f"Summary object {summary_obj}")

        one_line_summary = summary_obj["oneSentenceSummary"]
        bullet_points = summary_obj["summaryInNumericBulletPoints"]
        entities = summary_obj["entities"]
        concepts = summary_obj["concepts_ideas"]
    except Exception as e:
        logging.error(f"Error generating with LLM {e}")
        doc.status = "Failure"
        update_document(doc)
        return

    try:
        if one_line_summary:
            doc.short_summary = one_line_summary
        else:
            doc.short_summary = "No summary was generated"

        if bullet_points:
            doc.summary_bullet_points = bullet_points
        else:
            doc.summary_bullet_points = ["No bullet points were generated"]

        if entities:
            new_entities = []
            for entity in entities:
                new_entity = Entity()
                new_entity.document_id = doc.id
                new_entity.name = entity["name"]
                new_entity.description = entity["explanation"]
                new_entity.type = entity["type"]
                new_entity.source = mixtralClient._model_name
                new_entities.append(new_entity)

        if concepts:
            new_concepts = []
            for concept in concepts:
                new_concept = Concept()
                new_concept.document_id = doc.id
                new_concept.name = concept["concept"]
                new_concept.description = concept["explanation"]
                new_concept.source = mixtralClient._model_name
                new_concepts.append(new_concept)

        doc.update_at = datetime.datetime.now()
        doc.status = "Done"

        update_document(doc, [new_entities, new_concepts])

    except Exception as e:
        doc.status = "Failure"
        logging.error(f"Error generating with LLM {e}")
        update_document(doc)


def create_bookmark(page: Page) -> Bookmark:
    session = Session(engine)

    # Check if document exists, retrieve the bookmark and return
    # if exists. Else, create the document, bookmark.
    user_id = config["DUMMY_USER"]

    bookmark = session.scalar(
        select(Bookmark).where(
            and_(Bookmark.url == page.clean_url, Bookmark.user_id == int(user_id))
        )
    )

    if bookmark:
        logging.info(f"Bookmark from url {page.clean_url} already exists")
        session.close()
        return bookmark

    doc = create_document(page)

    bookmark = Bookmark()
    bookmark.url = page.clean_url
    bookmark.update_at = datetime.datetime.now()
    bookmark.document_id = doc.id

    session.add(bookmark)
    session.commit()
    session.refresh(bookmark)
    logging.info(f"Bookmark was created with id {bookmark.id}")

    session.close()

    return bookmark


def get_bookmarks_by_user_id(user_id: int) -> list[Bookmark]:
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


def get_entities_by_document_id(document_id) -> list[Entity]:
    session = Session(engine)
    entities = session.scalars(
        select(Entity).where(Entity.document_id == document_id)
    ).all()
    session.close()
    return entities


def get_concepts_by_document_id(document_id) -> list[Concept]:
    session = Session(engine)
    concepts = session.scalars(
        select(Concept).where(Concept.document_id == document_id)
    ).all()
    session.close()
    return concepts
