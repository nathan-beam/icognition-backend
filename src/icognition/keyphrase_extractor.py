from transformers.pipelines import AggregationStrategy
from transformers import (
    TokenClassificationPipeline,
    AutoModelForTokenClassification,
    AutoTokenizer
)
from icog_util import remove_stop_words, translator
import torch


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

    def add_context_to_keyphrase(self, keyphrase, text, wordpeding=3):
        """This method adds context to the keyphrases by looking at the text before and after the keyphrases.

        Args:
            keyphrase: dictionary that contains the keyphrase from KeyphraseExtractionPipeline
            text (str): text from which the keyphrases were extracted
        """
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

            keyphrase['context'] = f"{before} {keyword} {after}"
        else:
            keyphrase['context'] = keyphrase['word']

        return keyphrase

    def __call__(self, text) -> list:
        """This method extracts keyphrases from text.

        Args:
            text (str): text from which the keyphrases should be extracted
        """
        keyphrases = self.pipeline(text)
        for keyphrase in keyphrases:
            # Cast score to float to prevent JSON serialization errors and database problems
            keyphrase['score'] = float(keyphrase['score'])
            self.add_context_to_keyphrase(keyphrase, text)

        return keyphrases


if __name__ == '__main__':
    text = """on july 4th in the oval office, 
    the presedent of the USA sign the new low in front of statemens from England and the Netherlands."""
    extractor = KeyphraseExtraction()
    for keyphrase in extractor(text):
        print(keyphrase)
