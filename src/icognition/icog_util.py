
from stop_words import get_stop_words
from nltk.tokenize import word_tokenize
from typing import Union
from pydantic import BaseModel
import logging
import sys
import string


logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

translator = str.maketrans('', '', string.punctuation)
stop_words = get_stop_words('en')


def remove_stop_words(string, return_format='String'):
    """This method removes stop words from a string.

    Args:
        string (str): string from which the stop words should be removed
        return_format (str, optional): format of the returned data type String or List. Defaults to 'String'.

    Returns:
        str: string without stop words
    """
    tokens = word_tokenize(string)
    filtered_tokens = [w for w in tokens if not w in stop_words]

    if (return_format == 'List'):
        return filtered_tokens
    else:
        return ' '.join(filtered_tokens)


class textBlob(BaseModel):
    source: Union[str, None] = None
    text: str


class Page(BaseModel):
    url: Union[str, None] = None
    title: Union[str, None] = None
    clean_url: Union[str, None] = None
    paragraphs: Union[dict, None] = None
    summarized_paragraphs: Union[list, None] = None
    key_concepts: Union[list, None] = None
    full_text: Union[str, None] = None


if __name__ == '__main__':
    text = "city in the region of Southern Savonia in Finland"
