import datetime
import sys
import logging
import os, re
from app import html_parser
from app.db_connector import get_engine
from app.models import Bookmark, Entity, Page, Document, PagePayload, DocumentDisplay
from app.together_api_client import (
    TogetherMixtralOpenAIClient,
    TogetherMixtralClient,
    ApiCallException,
)
from sqlalchemy import (
    select,
    delete,
    create_engine,
    and_,
    or_,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Session


logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

env_vers = os.environ

engine = get_engine()

mixtralClient = TogetherMixtralClient()


def test_db_connection():

    try:
        conn = engine.connect()
        conn.close()
        return True
    except sqlalchemy.exc.OperationalError as e:
        logging.error(f"Error connectiong to DB {e}")
        return None


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


def delete_all_of_users_records(user_id: str) -> None:
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
    doc.title = page.title.strip()
    doc.url = page.clean_url
    doc.original_text = page.full_text
    session.add(doc)
    session.commit()
    session.refresh(doc)
    session.close()

    return doc


def clone_document(doc: Document):

    old_doc = get_document_by_id(doc.id)

    ## Clone document. This is used when regenerasting a document, we keep the old document and it's related objects
    new_doc = Document()
    new_doc.title = old_doc.title
    new_doc.url = old_doc.url
    new_doc.original_text = old_doc.original_text

    with Session(engine) as session:
        session.add(new_doc)
        session.commit()
        session.refresh(new_doc)

        # Update the old document to show it was cloned
        old_doc.status = "Cloned"
        return new_doc


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


def reassociate_bookmark_with_document(old_document_id, new_document_id):
    """
    This function reassociate a bookmark with a new document
    """
    with Session(engine) as session:
        bookmark = session.scalar(
            select(Bookmark).where(Bookmark.document_id == old_document_id)
        )
        if bookmark is None:
            logging.error(f"Bookmark with document {old_document_id} not found")
            return None

        bookmark.document_id = new_document_id
        bookmark.cloned_documents.append(old_document_id)

        session.commit()
        session.refresh(bookmark)
        logging.info(
            f"Bookmark {bookmark.id} reassociated with document {new_document_id}"
        )
        return bookmark


async def extract_info_from_doc(doc: Document):
    """
    Function that takes pages and return a document with the generated summary,
    bullet points and entities generate by LLM
    """

    doc.status = "Processing"
    update_document(doc)

    try:
        logging.info(f"Generating summary for document {doc.id}")
        response = await mixtralClient.generate(doc.original_text)
        logging.info(f"Response from LLM {response}")

    except ApiCallException as e:
        logging.error(f"Error generating with LLM {e}")
        ## TODO store exception in DB

        doc.status = "Api Failure"
        update_document(doc)
        return

    except Exception as e:
        logging.error(f"Error generating with LLM {e}")
        doc.status = "Failure"
        update_document(doc)
        return

    try:
        if response.oneSentenceSummary:
            doc.short_summary = response.oneSentenceSummary
        else:
            doc.short_summary = "No summary was generated"

        if response.summaryInNumericBulletPoints:
            doc.summary_bullet_points = [
                re.sub(r"[1-9]{,2}\.", "", point).strip()
                for point in response.summaryInNumericBulletPoints
            ]

        else:
            doc.summary_bullet_points = ["No bullet points were generated"]

        if response.usage:
            doc.llm_service_meta = response.usage

        if response.entities_and_concepts:
            new_entities = []
            for entity in response.entities_and_concepts:
                new_entity = Entity()
                new_entity.document_id = doc.id
                new_entity.name = entity.name
                new_entity.description = entity.explanation
                new_entity.type = entity.type
                new_entity.source = mixtralClient._model_name
                new_entities.append(new_entity)

        logging.info(f"LLM ussage was {response.usage}")

        doc.update_at = datetime.datetime.now()
        doc.status = "Done"

        return update_document(doc, [new_entities])

    except Exception as e:
        doc.status = "Failure"
        logging.error(f"Error generating with LLM {e}")
        update_document(doc)


def create_bookmark(page: Page, user_id: str) -> Bookmark:
    session = Session(engine)

    # Check if document exists, retrieve the bookmark and return
    # if exists. Else, create the document, bookmark.

    bookmark = session.scalar(
        select(Bookmark).where(
            and_(Bookmark.url == page.clean_url, Bookmark.user_id == user_id)
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
    bookmark.user_id = user_id

    session.add(bookmark)
    session.commit()
    session.refresh(bookmark)
    logging.info(f"Bookmark was created with id {bookmark.id}")

    session.close()

    return bookmark


def get_bookmarks_by_user_id(user_id: str) -> list[Bookmark]:
    session = Session(engine)
    bookmarks = session.scalars(
        select(Bookmark)
        .where(Bookmark.user_id == user_id)
        .order_by(Bookmark.update_at.desc())
    ).all()
    session.close()
    return bookmarks


def get_bookmark_by_document_id(document_id: int) -> Bookmark:
    session = Session(engine)
    bookmark = session.scalar(
        select(Bookmark).where(Bookmark.document_id == document_id)
    )
    session.close()
    return bookmark


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


def get_entities_by_user_id(user_id: str) -> list[Entity]:
    session = Session(engine)
    entities = session.scalars(
        select(Entity)
        .join(Document, Document.id == Entity.document_id)
        .join(Bookmark, Bookmark.document_id == Document.id)
        .where(Bookmark.user_id == user_id)
    ).all()
    session.close()
    return entities


def get_entities_by_user_id_and_type(user_id: str, type: str) -> list[Entity]:
    session = Session(engine)
    entities = session.scalars(
        select(Entity)
        .join(Document, Document.id == Entity.document_id)
        .join(Bookmark, Bookmark.document_id == Document.id)
        .where(Bookmark.user_id == user_id, Entity.type == type)
    ).all()
    session.close()
    return entities


def get_documenets_by_entity_id(entity_id: int) -> list[Document]:
    session = Session(engine)
    documents = session.scalars(
        select(Document)
        .join(Entity, Entity.document_id == Document.id)
        .where(Entity.id == entity_id)
    ).all()
    session.close()
    return documents


def get_entities_tree_by_user_id(user_id: str) -> list:
    session = Session(engine)
    queryTypes = text(
        """select e.type 
	            from entity e
	            join document d on e.document_id = d.id
	            join bookmark b on b.document_id = d.id
	            where b.user_id = '{USER_ID}'
	        group by 1""".format(
            USER_ID=user_id
        )
    )

    types = session.execute(queryTypes).fetchall()
    nodes = []
    for index, type in enumerate(types):
        node = {}
        node["key"] = str(index)
        node["label"] = type[0]
        node["data"] = type[0] + " folder"
        node["children"] = []

        entities_nodes = get_entities_by_user_id_and_type(user_id, type[0])
        for index2, entity in enumerate(entities_nodes):
            entity_node = {}
            entity_node["key"] = node["key"] + "-" + str(index2)
            entity_node["label"] = entity.name
            entity_node["data"] = entity.name + " entity"
            entity_node["children"] = []

            node["children"].append(entity_node)

            documents = get_documenets_by_entity_id(entity.id)
            for index3, document in enumerate(documents):
                document_node = {}
                document_node["key"] = entity_node["key"] + "-" + str(index3)
                document_node["label"] = document.title
                document_node["data"] = document.title + " document"
                entity_node["children"].append(document_node)
        nodes.append(node)

    session.close()
    return nodes


def search_documents(user_id: str, search_term: str = None) -> list[Document]:
    session = Session(engine)

    if search_term is None:
        documents = session.scalars(
            select(Document)
            .join(Bookmark, Bookmark.document_id == Document.id)
            .filter(Bookmark.user_id == user_id)
        ).all()
    else:
        documents = session.scalars(
            select(Document)
            .join(Bookmark, Bookmark.document_id == Document.id)
            .filter(
                Bookmark.user_id == user_id,
                or_(
                    Document.title.ilike(f"%{search_term}%"),
                    Document.short_summary.ilike(f"%{search_term}%"),
                ),
            )
        ).all()

    session.close()

    results = []
    for document in documents:
        entities = get_entities_by_document_id(document.id)
        display = DocumentDisplay.from_orm(document, entities=entities)
        results.append(display)

    return results
