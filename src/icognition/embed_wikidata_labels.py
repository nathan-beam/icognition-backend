from keyphrase_extractor import KeyphraseExtraction
from icog_util import remove_stop_words
from sentence_transformers import SentenceTransformer, util

sentance_transformer = SentenceTransformer(
    'paraphrase-MiniLM-L6-v2')
keyphrase_extractor = KeyphraseExtraction()


def add_context_to_wikidata_label(label, description):
    """This method adds context to short wikidata item label 
    by adding keyphrase from the description to the text. 
    This method is used by the embedd wikidata label.

    Args:
        label (str): label of the wikidata entity
        description (str): description of the wikidata entity
    """
    result = ''
    if (len(label.split(' ')) < 2):
        # logging.info(f"Adding context to {label} with description {description}")
        keyphrases = keyphrase_extractor(description)

        "Adding keyphrase to short label to add context to the label."
        result = label
        if (len(keyphrases) > 0):
            for keyphrase in keyphrases:
                """
                If the keyphrase score is higher than 0.8, we add the keyphrase to the label.
                """
                if (keyphrase.get('score') > 0.8):
                    result += ' ' + keyphrase.get('word')

        """
        If there is no keyphrase in the description, 
        we add remove stop words from the description and add the first 4 words to the label.
        """
        if (result == label):
            result += remove_stop_words(description, return_format='list')[:4]

    return result


def embedd_wikidata_label(label, description) -> dict:
    """This method generate embeeding from wikidata label and description of the entity."""

    text = add_context_to_wikidata_label(label, description)
    vector = sentance_transformer.encode(
        text, show_progress_bar=False)

    return {"text": text, "embedding": vector}
