import unittest
import icog_util as util
import json
from embed_wikidata_labels import add_context_to_wikidata_label
from keyphrase_extractor import KeyphraseExtraction
from transformer_text_summarizer import Summarizer
from app_logic import generate_keyphrases

path_file = '/home/eboraks/Projects/icognition_backend/data/icog_pages/bergum.medium.com%2Ffour-mistakes-when-introducing-embeddings-and-vector-search-d39478a568c5.json'
with open(path_file, 'r') as f:
    page = json.load(f)

summarizer = Summarizer()
keyphrases = KeyphraseExtraction()


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
        keyphrase['context'] = "oval office presedent USA sign new low"
        self.assertDictEqual(keyphrases.add_context_to_keyphrase(
            keyphrase, description), keyphrase)

    def test_keyphrases_extraction(self):
        text = """on july 4th in the oval office, 
                the presedent of the USA sign the new low in 
                front of statemens from England and the Netherlands."""

        self.assertEqual(len(keyphrases(text)), 3)

    def test_summarize_paragraphs(self):
        paragraphs = [v for k, v in page['paragraphs'].items()]
        summaries = summarizer(paragraphs)
        self.assertEqual(len(summaries), 3)

    def test_summarize_paragraphs_short(self):
        paragraphs = [v for k, v in page['paragraphs'].items()]
        summaries = summarizer(paragraphs, summary_length='first_chunk')
        self.assertEqual(len(summaries), 1)

    def test_keyphrases_extraction(self):
        text = """on july 4th in the oval office, 
                the presedent of the USA sign the new low in 
                front of statemens from England and the Netherlands."""

        self.assertEqual(len(generate_keyphrases(text)), 3)


if __name__ == '__main__':
    unittest.main()
