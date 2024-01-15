import app.app_logic as app_logic
import time

url = "https://www.yahoo.com/finance/news/collecting-degrees-thermometer-atlanta-woman-110000419.html"


def test_create_page():
    page = app_logic.create_page(url)
    assert page != None


async def test_bookmark_page():
    # Check if bookmark already exist, if yes delete it.
    # This is make the test more realistic.
    bookmark = app_logic.get_bookmark_by_url(url)
    if bookmark:
        app_logic.delete_bookmark_and_associate_records(bookmark.id)

    page = app_logic.create_page(url)
    bm = app_logic.create_bookmark(page)
    bookmark = app_logic.get_bookmark_by_url(url)
    assert bookmark != None

    doc = app_logic.get_document_by_id(bookmark.document_id)
    assert doc.id != None
    assert doc.url == url
    assert len(doc.original_text) > 0
    assert type(doc.original_text) == str

    # store the docuement id for future method
    document_id = doc.id
    app_logic.extract_info_from_doc(doc)

    # Testing the retrivel of document from the database
    doc = None
    doc = app_logic.get_document_by_id(document_id)

    # Testing the LLM extraction worked
    assert doc != None


def test_get_concets_by_document_id():
    bookmark = app_logic.get_bookmark_by_url(url)
    doc = app_logic.get_document_by_id(bookmark.document_id)
    concepts = app_logic.get_concepts_by_document_id(doc.id)
    assert len(concepts) > 0
    assert concepts[0].document_id == doc.id
    assert type(concepts) == list


def test_get_entities_by_document_id():
    bookmark = app_logic.get_bookmark_by_url(url)
    doc = app_logic.get_document_by_id(bookmark.document_id)
    entities = app_logic.get_entities_by_document_id(doc.id)
    assert len(entities) > 0
    assert entities[0].document_id == doc.id
    assert type(entities) == list
