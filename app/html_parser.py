import requests
import logging
import re
from lxml import html
from bs4 import BeautifulSoup
from app.models import Page
import urllib.parse as urlparse


logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.DEBUG,
)

logger = logging.getLogger(__name__)

MININUM_PARAGRAPH_LENGTH = 10


def get_webpage(url: str) -> BeautifulSoup:
    """_summary_

    Args:
        url (str): URL of the page

    Returns:
        BeautifulSoup: BeatifulSoup object
    """
    try:
        response = requests.get(url)
        content = response.text
        soup = BeautifulSoup(content, "lxml")
        return soup
    except Exception as e:
        logging.error(f"Error getting webpage: {url} with error: {e}")
        return None


def get_paragraphs(soup: BeautifulSoup) -> list[str]:
    articles = soup.find_all("article")

    content_estimator = []
    for article in articles:
        num_contect_ele = len(article.find_all("h1")) + len(article.find_all("p"))
        content_estimator.append(num_contect_ele)

    logging.info(content_estimator)
    if max(content_estimator) < 3:
        logging.warning("Not enought content on the page")
        raise ValueError("Not enough contect on the page")

    # Select the article element with the most content
    main_article = articles[content_estimator.index(max(content_estimator))]

    header_pattern = re.compile(r"h\d")
    text_elements = []
    for element in main_article.find_all(["p", "h1", "h2", "h3"]):
        ## Collect only paragraph and headers with enough content
        if element.name == "p" and len(element.text.split(" ")) > 8:
            text_elements.append(element.text)
        elif header_pattern.match(element.name) and len(element.text.split(" ")) > 3:
            text_elements.append(element.text)
        else:
            None
    return text_elements


def get_title(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    if h1 is None:
        logging.error("No title found in webpage")
        return None

    return h1.text


def extract_author_medium(soup: BeautifulSoup) -> str:
    author = soup.find(attrs={"data-testid": "authorName"}).text
    return author


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
    author = extract_author_medium(html)

    page = Page()
    page.clean_url = url
    page.paragraphs = paragraphs
    page.author = author
    page.full_text = "\n".join(paragraphs)
    page.title = title

    return page


if __name__ == "__main__":
    url = "https://bergum.medium.com/four-mistakes-when-introducing-embeddings-and-vector-search-d39478a568c5#tour"
    tree = get_webpage(url)
    paragraphs = get_paragraphs(tree)
    title = get_title(tree)
    author = extract_author_medium(tree)
    print(f"Title: {title}")
    print(f"Author: {author}")
    for paragraph in paragraphs:
        print("-----------------")
        print(paragraph)
