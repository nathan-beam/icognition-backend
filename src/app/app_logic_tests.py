import unittest
from pydantic_models import Page
import app_logic
import json
import icog_util as util
from embed_wikidata_labels import add_context_to_wikidata_label
from keyphrase_extractor import KeyphraseExtraction
from transformer_text_summarizer import Summarizer
from keyphrase_extractor import KeyphraseExtraction


url = "https://bergum.medium.com/four-mistakes-when-introducing-embeddings-and-vector-search-d39478a568c5#tour"
page = app_logic.create_page(url)

summarizer = Summarizer()
keyphrase_extractor = KeyphraseExtraction()

# Global bookmark to be used in tests of bookmark, document and keyphrase creation and retrieval
global_bookmark = None


class TestUtil(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestUtil, self).__init__(*args, **kwargs)

    def test_remove_stop_words(self):
        text = "Nick likes to play football however he is not too fond of tennis"
        answer = "Nick likes play football however fond tennis"
        self.assertEqual(util.remove_stop_words(text), answer)

    def test_add_context_to_wikidata_label(self):
        label = "Mikkeli"
        description = "city in the region of Southern Savonia in Finland"
        answer = "Mikkeli savonia finland"
        self.assertEqual(add_context_to_wikidata_label(
            label, description), answer)

    def test_add_context_to_keyphrase(self):
        description = "on july 4th in the oval office, the presedent of the USA sign the new low in front of statemens from both parties"
        keyphrase = {"word": "USA", "start": 53,
                     "end": 56, "score": 0.99, "type": "entity"}
        context = "oval office presedent USA sign new low"
        self.assertEqual(
            keyphrase_extractor.extract_context(keyphrase, description),
            context)

    def test_keyphrases_extraction(self):
        text = """on july 4th in the oval office, 
                the presedent of the USA sign the new low in 
                front of statemens from England and the Netherlands."""

        self.assertEqual(len(keyphrase_extractor(text)), 3)

    def test_summarize_paragraphs(self):
        summaries = summarizer(page.paragraphs)
        self.assertEqual(len(summaries), 3)

    def test_summarize_paragraphs_short(self):

        summaries = summarizer(page.paragraphs, summary_length='first_chunk')
        self.assertEqual(len(summaries), 1)

    def test_generate_bookmark(self):
        global_bookmark = app_logic.generate_bookmark(page)
        self.assertEqual(global_bookmark.url, page.clean_url)

    def test_get_document(self):
        document = app_logic.get_document_by_url(page.clean_url)
        self.assertEqual(document.url, page.clean_url)

    def test_get_keyphrase(self):
        keyphrases = app_logic.get_keyphrases_by_document_url(
            page.clean_url)
        print(f'Number of keyphrases: {len(keyphrases)}')
        self.assertGreater(len(keyphrases), 3)

    def test_create_page(self):
        page = app_logic.create_page(url)
        self.assertNotEqual(page.clean_url, url)
        self.assertIsNotNone(page.paragraphs)
        self.assertIsNotNone(page.title)


if __name__ == '__main__':
    unittest.main()
