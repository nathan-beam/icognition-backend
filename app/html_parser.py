import requests
import logging
import sys
import urllib.parse
import re
from lxml import html
from app.models import Page

logging.basicConfig(format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)

MININUM_PARAGRAPH_LENGTH = 10


def get_webpage(url) -> html.HtmlElement:
    """_summary_

    Args:
        url (_type_): _description_

    Returns:
        html.HtmlElement: _description_
    """
    try:
        response = requests.get(url)
        content = response.content
        tree = html.fromstring(content)
        return tree
    except Exception as e:
        logging.error(f"Error getting webpage: {e}")
        return None


def get_paragraphs(tree: html.HtmlElement) -> list[str]:
    text = []
    # //article//h1|//h2|//p[string-length( text()) > 20]|//ul//li[string-length( text()) > 20]
    t = tree.xpath("//article//p|//h2|//h3")

    p_counter = 0
    h2_counter = 0
    for i in t:
        if i.tag == "p" and i.text is not None:
            # Remove paragraphs that are too short
            if len(i.text.split(' ')) > MININUM_PARAGRAPH_LENGTH:
                text.append(i.text)
                p_counter += 1
        elif i.tag == "h2" and i.text is not None:
            text.append(i.text)
            h2_counter += 1
        elif i.tag == "h3" and i.text is not None:
            text.append(i.text)

    if (p_counter < 2 and h2_counter < 1):
        logging.error("Not enough paragraphs or h2 tags in webpage")
        return None
    return text


def get_title(tree: html.HtmlElement) -> str:
    return tree.xpath("//article//h1")[0].text


def clean_url(url: str) -> str:
    """Clean URL from trailing characters

    Args:
        url (str): _description_

    Returns:
        str: _description_
    """

    # Define the regex
    page_regex = r"(http.*:\/\/[a-zA-Z0-9:\/\.\-]*)"

    # Match the regex against the URL
    matches = re.findall(page_regex, url)

    # Get the first match
    clean_url = matches[0]

    # If no match, use the URL as the page URL
    if not clean_url:
        return url
    else:
        # Encode the URL and return it
        return clean_url


def create_page(url) -> Page:
    url = clean_url(url)
    html = get_webpage(url)
    paragraphs = get_paragraphs(html)

    if (paragraphs is None):
        logging.error("No paragraphs found in webpage")
        return None

    title = get_title(html)

    page = Page()
    page.clean_url = url
    page.paragraphs = paragraphs
    page.full_text = "\n".join(paragraphs)
    page.title = title

    return page


if __name__ == "__main__":
    url = "https://bergum.medium.com/four-mistakes-when-introducing-embeddings-and-vector-search-d39478a568c5#tour"
    tree = get_webpage(url)
    paragraphs = get_paragraphs(tree)
    title = get_title(tree)
    print("Title")
    print(title)
    for paragraph in paragraphs:
        print("-----------------")
        print(paragraph)
