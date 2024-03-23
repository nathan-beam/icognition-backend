import time
import requests
import urllib.parse as urlparse
from typing import List

""" Generate unit test for endpoints.py FastAPI functions """


base_url = (
    "https://icognition-api-scv-5csjr6fjpa-uc.a.run.app"  # "http://127.0.0.1:8889"
)

url = "https://www.yahoo.com/sports/march-madness-no-11-duquesne-upsets-no-6-byu-for-first-tournament-win-in-over-50-years-185918242.html"
payload = {"url": url, "user_id": "7778888"}

# Unit test for create bookmart


# use requests to call /bookmark endpoint with jpage as payload
# check response status code
# check response content
def test_bookmark_end_to_end_workflow():
    url = urlparse.quote(payload["url"], safe="")
    params = {"url": url}
    response = requests.get(f"{base_url}/bookmark", params=params)
    status_code = response.status_code
    if status_code == 200:
        bookmark_id = response.json()["id"]
        response = requests.delete(f"{base_url}/bookmark/{bookmark_id}/document")
        status_code = response.status_code
        assert status_code == 204

    response = requests.post(f"{base_url}/bookmark", json=payload)
    assert response.status_code == 201
    bookmark_id = response.json()["id"]
    document_id = response.json()["document_id"]
    assert bookmark_id != None

    url = urlparse.quote(payload["url"], safe="")
    params = {"url": url}
    response = requests.get(f"{base_url}/bookmark", params=params)
    status_code = response.status_code
    assert status_code == 200

    response = requests.get(f"{base_url}/bookmark/{bookmark_id}/document")
    status_code = response.status_code
    assert status_code == 200
    # URL that is returned is was normalized
    # so it is not equal to the original URL
    # but it is a substring of the original URL
    doc = response.json()
    assert len(doc["url"]) <= len(url)

    response = requests.get(f"{base_url}/document/{document_id}")
    status_code = response.status_code
    assert status_code == 200

    # get entities and concepts related to document
    entities_res = requests.get(f"{base_url}/document/{document_id}/entities")
    assert entities_res.status_code == 200
    entities = entities_res.json()
    assert len(entities) > 0
    concepts_res = requests.get(f"{base_url}/document/{document_id}/concepts")
    assert concepts_res.status_code == 200
    concepts = concepts_res.json()
    assert len(concepts) > 0


def test_create_bookmark_not_found():
    url = urlparse.quote("https://www.google.com", safe="")
    payload = {"url": url}
    response = requests.post(f"{base_url}/bookmark", json=payload)
    status_code = response.status_code
    assert status_code == 204


def test_get_bookmark_not_found():
    url = urlparse.quote("https://www.google.com", safe="")
    params = {"url": url}
    response = requests.get(f"{base_url}/bookmark", params=params)
    print(f"Test get bookmark not found response {response.json()}")
    status_code = response.status_code
    assert status_code == 404


def test_get_bookmarks_per_user():
    response = requests.get(f"{base_url}/bookmark/user/777")
    assert response.status_code == 200
    bookmarks = response.json()
    assert len(bookmarks) > 0


def xtest_get_document():
    response = requests.post(f"{base_url}/bookmark", json=payload)
    id = response.json()["document_id"]
    response = None
    response = requests.get(f"{base_url}/document/{id}")
    assert response.status_code == 200


def test_document_regeration():
    ## get document by url
    bookmark_response = requests.get(f"{base_url}/bookmark", params={"url": url})
    bookmark = bookmark_response.json()
    assert bookmark != None

    # get document by document id
    doc_response = requests.get(f"{base_url}/document/{bookmark['document_id']}")
    doc = doc_response.json()
    assert doc != None

    # regenerate document
    doc["status"] = "Done"
    new_doc_response = requests.post(f"{base_url}/document/", json=doc)
    assert new_doc_response.status_code == 202
    new_doc = new_doc_response.json()
    assert new_doc != None

    bookmark_response = requests.get(f"{base_url}/bookmark", params={"url": url})
    bookmark2 = bookmark_response.json()
    assert bookmark2["cloned_documents"] != None
    assert bookmark2["document_id"] != new_doc["id"]
