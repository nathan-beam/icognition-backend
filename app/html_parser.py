import requests
import logging
import re
from lxml import html
from app.models import Page
import urllib.parse as urlparse


logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.DEBUG,
)

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
        content = response.text
        htmlpage = html.fromstring(content)
        return htmlpage
    except Exception as e:
        logging.error(f"Error getting webpage: {url} with error: {e}")
        return None


def get_paragraphs(htmlpage: html.HtmlElement) -> list[str]:
    text = []
    # //article//h1|//h2|//h3|//h4|//p|//ul//li
    elements = htmlpage.xpath("//article//p|//h2|//h3")

    p_counter = 0
    h_counter = 0
    for e in elements:
        if e.tag == "p" and e.text is not None:
            # Remove paragraphs that are too short
            if len(e.text.split(" ")) > MININUM_PARAGRAPH_LENGTH:
                text.append(e.text)
                p_counter += 1
        elif re.match(r"h\d", e.tag) and e.text is not None:
            text.append(e.text)
            h_counter += 1

    if p_counter < 2 and h_counter < 1:
        logging.error("Not enough paragraphs or h2 tags in webpage")
        return None
    return text


def get_title(htmlpage: html.HtmlElement) -> str:
    if htmlpage.xpath("//article//h1") == []:
        logging.error("No title found in webpage")
        return None

    return htmlpage.xpath("//article//h1")[0].text


def clean_url(url: str) -> str:
    """Clean URL from trailing characters

    Args:
        url (str): _description_

    Returns:
        str: _description_
    """
    url = urlparse.unquote(url)
    # Define the regex
    page_regex = r"(http.*:\/\/[a-zA-Z0-9:\/\.\-\@]*)"

    # Match the regex against the URL
    matches = re.findall(page_regex, url)

    # Get the first match
    if matches:
        clean_url = matches[0]
    else:
        # If no match, use the URL as the page URL
        clean_url = url

    return clean_url


def create_page(url) -> Page:
    url = clean_url(url)
    html = get_webpage(url)
    if html is None:
        logging.error("No webpage found")
        return None

    paragraphs = get_paragraphs(html)

    if paragraphs is None:
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
