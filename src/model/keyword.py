from .feature import Feature


class Keyword(Feature):
    TABLE_NAME = 'keyword'
    name: str
    _book: int
