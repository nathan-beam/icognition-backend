from app import html_parser

url = "https://www.yahoo.com/finance/news/collecting-degrees-thermometer-atlanta-woman-110000419.html"


def test_create_page():
    page = html_parser.create_page(url)
    assert type(page.full_text) == str
    assert len(page.full_text) > 0
    # assert len(page.author) > 1
