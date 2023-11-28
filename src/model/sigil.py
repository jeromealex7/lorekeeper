from .feature import Feature


class Sigil(Feature):
    TABLE_NAME = 'sigil'
    _encounter: int
    _page: int
    list_index: int
