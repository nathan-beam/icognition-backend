from transformers.pipelines import AggregationStrategy
from transformers import (
    TokenClassificationPipeline,
    AutoModelForTokenClassification,
    AutoTokenizer
)
from icog_util import remove_stop_words, translator
from sentence_transformers import SentenceTransformer
import torch


stantance_model_name = "paraphrase-MiniLM-L6-v2"
device = "cuda:0" if torch.cuda.is_available() else "cpu"
sentence_transformer = SentenceTransformer(stantance_model_name, device=device)


class KeyphraseExtractionPipeline(TokenClassificationPipeline):
    def __init__(self, model_name, *args, **kwargs):
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

    def __init__(self, model_name='ml6team/keyphrase-extraction-distilbert-inspec'):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.pipeline = KeyphraseExtractionPipeline(
            model_name=model_name, device=self.device)

    def extract_context(self, keyphrase, text, wordpeding=3) -> str:
        """This method adds context to the keyphrases by looking at the text before and after the keyphrases.

        Args:
            keyphrase: dictionary that contains the keyphrase from KeyphraseExtractionPipeline
            text (str): text from which the keyphrases were extracted
        Retrurn: 
            String that contains the context of the keyphrase
        """
        context = ''
        if (len(keyphrase['word'].split(' ')) <= 2):
            start_pos = keyphrase['start']
            end_pos = keyphrase['end']
            before, keyword, after = text.partition(
                text[start_pos:end_pos])
            before = before.translate(translator).strip()
            before = remove_stop_words(before)
            after = after.translate(translator).strip()
            after = remove_stop_words(after)
            if (len(after.split(' ')) > wordpeding):
                after = ' '.join(after.split(' ')[0:wordpeding])

            if (len(before.split(' ')) > wordpeding):
                before = ' '.join(before.split(' ')[-wordpeding:])

            context = f"{before} {keyword} {after}"
        else:
            context = keyphrase['word']

        return context

    def __call__(self, text) -> list:
        """This method extracts keyphrases from text.

        Args:
            text (str): text from which the keyphrases should be extracted
        """
        keyphrases = self.pipeline(text)
        for keyphrase in keyphrases:
            # Cast score to float to prevent JSON serialization errors and database problems
            keyphrase['score'] = float(keyphrase['score'])
            keyphrase['context'] = self.extract_context(keyphrase, text)
            keyphrase['word_vec'] = sentence_transformer.encode(
                keyphrase['word'], show_progress_bar=False)
            keyphrase['context_vec'] = sentence_transformer.encode(
                keyphrase['context'], show_progress_bar=False)

        return keyphrases


if __name__ == '__main__':
    text = """on july 4th in the oval office, 
    the presedent of the USA sign the new low in front of statemens from England and the Netherlands."""
    extractor = KeyphraseExtraction()
    for keyphrase in extractor(text):
        print(keyphrase)
