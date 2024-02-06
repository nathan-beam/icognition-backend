import requests
import logging
import re
from bs4 import BeautifulSoup
from app.models import Page, PagePayload
import urllib.parse as urlparse


logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.DEBUG,
)

logger = logging.getLogger(__name__)

MININUM_PARAGRAPH_LENGTH = 10


def get_webpage(payload: PagePayload) -> BeautifulSoup:
    """_summary_

    Args:
        url (str): URL of the page

    Returns:
        BeautifulSoup: BeatifulSoup object
    """
    try:

        if payload.html:
            logging.info("Html_parser -> get_webpage -> Using payload html")
            return BeautifulSoup(payload.html, "html.parser")

        logging.info("Html_parser -> get_webpage -> requests.get -> payload.url")
        response = requests.get(payload.url)
        content = response.text
        return BeautifulSoup(content, "html.parser")
    except requests.exceptions.InvalidSchema as e:
        logging.error(
            f"InvalidSchema wrror getting webpage: {payload.url} with error: {e}"
        )
        return None
    except Exception as e:
        logging.error(f"Error getting webpage: {payload.url} with error: {e}")
        return None


def get_paragraphs(soup: BeautifulSoup) -> list[str]:
    # HBS article tag: article = soup.select('div[class*="article-body"]')
    articles = soup.find_all("article")

    if articles == None:
        return None

    content_estimator = []
    for article in articles:
        num_contect_ele = len(article.find_all("h1")) + len(article.find_all("p"))
        content_estimator.append(num_contect_ele)

    if len(content_estimator) == 0:
        return None

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
    try:
        author = soup.find(attrs={"data-testid": "authorName"}).text
        return author
    except:
        logging.error(f"Cloud not extract author")


def clean_url(url: str) -> str:
    """Clean URL from trailing characters

    Args:
        url (str): _description_

    Returns:
        str: _description_
    """
    url = urlparse.unquote(url)
    # Define the regex
    page_regex = r"(http.*:\/\/[a-zA-Z0-9:\/\.\-\@\%\_]*)"

    # Match the regex against the URL
    matches = re.findall(page_regex, url)

    # Get the first match
    if matches:
        clean_url = matches[0]
    else:
        # If no match, use the URL as the page URL
        clean_url = url

    return clean_url


def create_page(payload: PagePayload) -> Page:

    html = get_webpage(payload)
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
    page.clean_url = clean_url(payload.url)
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
