from transformers.pipelines import AggregationStrategy
from transformers import (
    TokenClassificationPipeline,
    AutoModelForTokenClassification,
    AutoTokenizer,
    pipeline,
)
from sentence_transformers import SentenceTransformer, util
import numpy as np
import lancedb
import logging
import sys
import string

logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

# Define keyphrase extraction pipeline


class KeyphraseExtractionPipeline(TokenClassificationPipeline):
    def __init__(self, model_name="ml6team/keyphrase-extraction-distilbert-inspec", *args, **kwargs):
        super().__init__(
            model=AutoModelForTokenClassification.from_pretrained(model_name),
            tokenizer=AutoTokenizer.from_pretrained(model_name),
            *args,
            **kwargs
        )

    def postprocess(self, all_outputs):
        mid_results = super().postprocess(
            all_outputs=all_outputs,
            aggregation_strategy=AggregationStrategy.FIRST,
        )
        strings = set()
        results = []
        for kp in mid_results:
            if kp.get("word") not in strings:
                strings.add(kp.get("word"))
                results.append(kp)

        return results


class KeyphraseExtraction:
    def __init__(self,
                 model_name="ml6team/keyphrase-extraction-distilbert-inspec",
                 stantance_model_name="all-MiniLM-L6-v2",
                 db_path="/home/eboraks/Projects/icognition_backend/data/lance.db"):

        self.lance_db = lancedb.connect(db_path)
        self.ltable = self.lance_db.open_table("ldb_from_joined")
        self.sentence_transformer = SentenceTransformer(stantance_model_name)
        self.model_name = model_name
        self.keyphrase_extractor = KeyphraseExtractionPipeline(
            model_name=model_name)
        self.translator = str.maketrans('', '', string.punctuation)

    # TODO: using LanceDB and wikidata get the wikidata link
    def prune_keyphrases(self, keyphrases):
        pruned_keyphrases = []
        for kp in keyphrases:
            if kp['score'] > 0.5:
                pruned_keyphrases.append(kp)

        return pruned_keyphrases

    def search_for_wikidata_items(self, keyphrases):

        for kp in keyphrases:
            vector = self.get_sentence_embedding(kp.get("word"))
            hits = self.ltable.search(vector).limit(1).to_df()
            if (len(hits) > 0):
                hits['score'] = hits['score'].round(3)
                kp['wikidata_id'] = hits.iloc[0]['id']
                kp['wikidata_score'] = hits.iloc[0]['score']
                kp['wikidata_label'] = hits.iloc[0]['text']

        return keyphrases

    def add_context(self, keyphrases, text):
        for kp in keyphrases:
            if (len(kp['word'].split(' ')) <= 2):
                start_pos = kp['start']
                end_pos = kp['end']
                before, keyword, after = text.partition(
                    text[start_pos:end_pos])
                before = before.translate(self.translator).strip()
                after = after.translate(self.translator).strip()
                if (len(after.split(' ')) > 5):
                    after = after.split(' ')[0:5].join(' ')

                if (len(before.split(' ')) > 5):
                    before = before.split(' ')[-5:].join(' ')

                kp['context'] = f"{before} {keyword} {after}"
            else:
                kp['context'] = kp['word']

        return keyphrases

    def extract(self, text):
        keyphrases = []
        try:
            keyphrases = self.keyphrase_extractor(text)
            keyphrases = self.add_context(keyphrases, text)
            keyphrases = self.search_for_wikidata_items(keyphrases)
        except Exception as e:
            logging.error(e)

        return keyphrases


class SummarizeText:
    def __init__(self, model_name="pszemraj/led-base-book-summary"):
        self.model_name = model_name
        self.summarizer = pipeline("summarization", model=model_name)

    # TODO add machanism to handle long texts
    def summarize(self, text):
        summary = ''
        try:
            summary = self.summarizer(text)[0]['summary_text']
        except Exception as e:
            logging.error(e)

        return summary


if __name__ == '__main__':
    text = """The United States of America (USA), commonly known as the United States (U.S.) or America, 
    is a country comprising 50 states, a federal district, five major self-governing territories, 
    and various possessions."""

    summarizer = SummarizeText(model_name="pszemraj/led-base-book-summary")

    keyphrase_extractor = KeyphraseExtraction()
    keyphrases = keyphrase_extractor.extract(text)
    # pruned_keyphrases = keyphrase_extractor.prune_keyphrases(keyphrases)
    print(keyphrases)
    # print(summarizer.summarize(text))
