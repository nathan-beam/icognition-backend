import app.app_logic as app_logic
import time

url = "https://medium.com/@michaelgoitein/the-playing-to-win-framework-part-iii-the-strategy-choice-cascade-279c3b5ccea3"


def test_create_page():
    page = app_logic.create_page(url)
    assert page != None


def test_bookmark_page():
    # Check if bookmark already exist, if yes delete it.
    # This is make the test more realistic.
    bookmark = app_logic.get_bookmark_by_url(url)
    if bookmark:
        app_logic.delete_bookmark_and_associate_records(bookmark.id)

    page = app_logic.create_page(url)
    app_logic.create_bookmark(page)
    bookmark = app_logic.get_bookmark_by_url(url)
    assert bookmark != None

    doc = app_logic.get_document_by_id(bookmark.document_id)
    assert doc.id != None
    assert doc.url == url
    assert len(doc.original_text) > 0
    assert type(doc.original_text) == str

    # store the docuement id for future method
    document_id = doc.id
    app_logic.extract_meaning(doc)

    # Testing the retrivel of document from the database
    doc = None
    doc = app_logic.get_document_by_id(document_id)

    # Testing the LLM extraction worked
    assert doc != None
    assert type(doc.llama2_entities_raw) == str
    assert type(doc.summary_bullet_points) == str
    assert type(doc.concepts_generated) == str
    assert type(doc.spacy_entities_json) == list
    assert type(doc.title) == str
    assert type(doc.url) == str

    assert len(doc.llama2_entities_raw) > 20
    assert len(doc.summary_bullet_points) > 20
    assert len(doc.concepts_generated) > 20
    assert len(doc.spacy_entities_json) > 0
    assert len(doc.title) > 5
    assert len(doc.url) > 5
