import app.app_logic as app_logic

url = "https://medium.com/@michaelgoitein/the-playing-to-win-framework-part-iii-the-strategy-choice-cascade-279c3b5ccea3"


def test_create_page():
    page = app_logic.create_page(url)
    assert page != None


def test_bookmark_page():
    # Check if bookmark already exist, if yes delete it.
    # This is make the test more realistic.
    bookmark = app_logic.get_bookmark_by_url(url)
    if bookmark:
        app_logic.delete_document_and_associate_records(bookmark.document_id)

    page = app_logic.create_page(url)
    app_logic.generate_bookmark(page)
    bookmark = app_logic.get_bookmark_by_url(url)
    assert bookmark != None

    # Get document that was create with the bookmark
    document = app_logic.get_document_by_id(bookmark.document_id)
    assert document != None
    assert type(document.found_entities_raw) == str
    assert type(document.summary_bullet_points) == str
    assert type(document.summary_generated) == str
    assert type(document.title) == str
    assert type(document.url) == str

    assert len(document.found_entities_raw) > 20
    assert len(document.summary_bullet_points) > 20
    assert len(document.summary_generated) > 20
    assert len(document.title) > 5
    assert len(document.url) > 5
