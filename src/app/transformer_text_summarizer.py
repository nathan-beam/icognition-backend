from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
)
import torch


class Summarizer():
    """
    TransformerTextSummarizer class is used to generate summary from text.
    This code is inspired by a comment on https://discuss.huggingface.co/t/summarization-on-long-documents/920/21

    Args:
        model_key, huggingface model uri
        language, language of the text
    """

    def __init__(self, model_key='facebook/bart-large-cnn', language='en'):
        self._tokenizer = AutoTokenizer.from_pretrained(model_key)

        self._language = language

        self._model = AutoModelForSeq2SeqLM.from_pretrained(model_key)

        self._device = "cuda:0" if torch.cuda.is_available() else "cpu"

    def __chunk_text(self, paragraphs) -> list:
        """Generate chunk of tokens from a list of paragrams.

        Args:
            paragraphs (list): list of text paragrams

        Return: 
            chunks (list): list of text paragrams
        """

        chunks = []
        chunk = ''
        length = 0

        for paragraph in paragraphs:
            tokenized_sentence = self._tokenizer.encode(
                paragraph, truncation=False, max_length=None, return_tensors='pt')[0]

            if len(tokenized_sentence) > self._tokenizer.model_max_length:
                continue

            length += len(tokenized_sentence)

            if length <= self._tokenizer.model_max_length:
                chunk = chunk + ' ' + paragraph
            else:
                chunks.append(chunk.strip())
                chunk = paragraph
                length = len(tokenized_sentence)

        if len(chunk) > 0:
            chunks.append(chunk.strip())

        return chunks

    def __clean_text(self, text):
        if text.count('.') == 0:
            return text.strip()

        end_index = text.rindex('.') + 1

        return text[0: end_index].strip()

    def __call__(self, paragraphs: list, beams=5, summary_length='full', *args, **kwargs) -> list[str]:
        """Summarize text.

        Args:
            paragraphs (list)): list of text paragrams to be summarized
            beams (int): number of beams to use for the generation of the summary
            summary_length (str): length of the summary, can be 'full' or 'first_chunk'

        Return:
            summaries (list): list of summaries
        """

        chunk_texts = self.__chunk_text(paragraphs)
        chunk_summaries = []

        for chunk_text in chunk_texts:

            if (summary_length == 'first_chunk' and len(chunk_summaries) > 0):
                break

            input_tokenized = self._tokenizer.encode(
                chunk_text, return_tensors='pt')

            input_tokenized = input_tokenized.to(self._device)

            summary_ids = self._model.to(self._device).generate(
                input_tokenized,
                length_penalty=3.0,
                min_length=int(0.1 * len(chunk_text)),
                max_length=int(0.2 * len(chunk_text)),
                early_stopping=True,
                num_beams=beams,
                no_repeat_ngram_size=2)

            output = [self._tokenizer.decode(
                g, skip_special_tokens=True, clean_up_tokenization_spaces=True) for g in summary_ids]

            chunk_summaries.append(output)

        summaries = [self.__clean_text(
            text) for chunk_summary in chunk_summaries for text in chunk_summary]

        return summaries
