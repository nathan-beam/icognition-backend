from app import html_parser

url = "https://medium.com/@michaelgoitein/the-playing-to-win-framework-part-iii-the-strategy-choice-cascade-279c3b5ccea3"


def test_create_page():
    page = html_parser.create_page(url)
    assert type(page.full_text) == str
    assert len(page.full_text) > 0
    assert len(page.author) > 1
