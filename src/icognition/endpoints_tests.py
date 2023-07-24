import unittest
import json
import requests
""" Generate unit test for endpoints.py FastAPI functions """


base_url = 'http://localhost:8889'

url = "https://bergum.medium.com/four-mistakes-when-introducing-embeddings-and-vector-search-d39478a568c5#tour"
payload = {"url": url}

# Unit test for create bookmart


class TestEndpoints(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)

    # use requests to call /bookmark endpoint with jpage as payload
    # check response status code
    # check response content
    def test_create_bookmark(self):
        response = requests.post(f"{base_url}/bookmark", json=payload)
        self.assertIsNotNone(response.json()['id'])

    """
    Unit test to get document using document id from endpoint
    """

    def test_get_document(self):
        response = requests.post(f"{base_url}/bookmark", json=payload)
        id = response.json()['document_id']
        response = None
        response = requests.get(f"{base_url}/document/{id}")
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()['url'], payload['url'])

    def test_get_keyphrases(self):
        response = requests.post(f"{base_url}/bookmark", json=payload)
        id = response.json()['document_id']
        response = None
        response = requests.get(f"{base_url}/document/{id}/keyphrases")
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json()[0])
        self.assertEqual(response.json()[0]['document_id'], id)

    def test_full_document_workflow(self):

        bookmark_res = requests.post(f"{base_url}/bookmark", json=payload)
        self.assertEqual(bookmark_res.status_code, 200)
        print(bookmark_res.json())
        id = bookmark_res.json()['document_id']
        self.assertIsNotNone(id)

        document_res = requests.get(f"{base_url}/document/{id}")
        self.assertEqual(document_res.status_code, 200)
        self.assertIsNotNone(document_res.json())
        self.assertIsNotNone(document_res.json()['summary_generated'])

        keyphrases_res = requests.get(f"{base_url}/document/{id}/keyphrases")
        self.assertEqual(keyphrases_res.status_code, 200)
        self.assertIsNotNone(keyphrases_res.json())
        self.assertGreater(len(keyphrases_res.json()), 1)

        delete_res = requests.delete(f"{base_url}/document/{id}/cascade")
        self.assertEqual(delete_res.status_code, 204)


if __name__ == '__main__':
    unittest.main()
