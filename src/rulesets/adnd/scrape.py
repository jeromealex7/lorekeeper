import html
import itertools
import json
import re
import requests
import time
from typing import Collection

from .adnd import ADnD
from .constants import MONSTER_TABLE
from src.model import Keep
from src.settings import PATHS

REGEX_BOOK = re.compile(r'<a class="bookcard-module--book-link--0cee9" href="/catalog/(.*?)/">')
REGEX_IMAGE = re.compile(r'"(/images/monsters/img/bookworm.gif)"')
REGEX_LINK = re.compile(r'<a class="book-module--list-link--2a6a4" href="(/catalog/.*?)">')
REGEX_NAMES = re.compile(r'<th class="cn">(.*?)</th>')
REGEX_REMOVE_HTML = re.compile(r'</?[au].*?>')
REGEX_TEXT = re.compile(r'<table.*?</table>(.*?)<br', re.DOTALL)
REGEX_TITLE = re.compile(r'aria-current="page" .*?>(.*?)<!--')
SETTINGS = ('add2_01', 'fr')
URL = r'https://www.completecompendium.com'


def get_keyword(key: str, text: str) -> tuple[str, ...]:
    regex_key = re.compile(rf'<tr><th>{key}:</th>(.*?)</tr>', re.IGNORECASE)
    regex_result = re.compile(r'<td>(.*?)</td>', re.IGNORECASE)
    try:
        results = regex_key.search(text).groups()[0]
    except AttributeError:
        return ()
    return tuple(re.sub('<.*?>', '', match.groups()[0]) for match in regex_result.finditer(results))


def iter_book(book: str) -> iter:
    catalog_url = f'{URL}/catalog/{book}/'
    answer = requests.get(catalog_url)
    text = answer.text
    for monster_html in iter_links(text):
        yield monster_html


def iter_catalog() -> iter:
    catalog_url = f'{URL}/catalog/'
    for setting in SETTINGS:
        answer = requests.get(catalog_url + setting)
        setting_html = answer.text
        for match in REGEX_BOOK.finditer(setting_html):
            book_name = match.groups()[0]
            yield book_name


def iter_links(text: str) -> iter:
    return (requests.get(f'{URL}{match.groups()[0]}').text for match in REGEX_LINK.finditer(text))


def read_html(html_text: str) -> tuple | None:
    entry: dict[str, tuple[str, ...]] = {}
    names = tuple(match.groups()[0] for match in REGEX_NAMES.finditer(html_text))
    count = len(names) or 1
    for html_key, entry_key in MONSTER_TABLE:
        entry[entry_key] = get_keyword(html_key, html_text)
    try:
        text = REGEX_TEXT.search(html_text).groups()[0]
        title = REGEX_TITLE.search(html_text).groups()[0]
    except (AttributeError, IndexError):
        return None

    def get_result(data: dict, index: int) -> dict[str, str | int] | None:
        try:
            n = f'{title} ({names[index]})'
        except IndexError:
            n = title
        try:
            result = {key: val[index] for key, val in data.items()}
        except IndexError:
            return None
        result['name'] = n
        result['text'] = REGEX_REMOVE_HTML.sub('', text)
        return result
    return tuple(filter(None, (get_result(entry, i) for i in range(count))))


def import_monsters(keep: Keep, books: str | Collection[str] = 'add2_01/2102'):
    if not books:
        books = iter_catalog()
    elif isinstance(books, str):
        books = (books,)
    data_path = PATHS['scrape'].joinpath('adnd.json')
    if data_path.exists():
        data = json.loads(data_path.read_text())
    else:
        data = list(filter(None, (read_html(monster_html) for monster_html in itertools.chain(*(iter_book(book)
                                                                                                for book in books)))))
        data_path.write_text(json.dumps(data))
    for monster_result in data:
        for monster in monster_result:
            guard = ADnD.GUARD_TYPE(keep)
            for key, val in monster.items():
                guard[key] = html.unescape(str(val))
            guard.commit()
        time.sleep(.4)
