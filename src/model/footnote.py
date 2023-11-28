from .feature import Feature


class Footnote(Feature):
    TABLE_NAME = 'footnote'
    _book: int
    _page: int
    list_index: int
