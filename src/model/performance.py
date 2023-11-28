from .feature import Feature


class Performance(Feature):
    TABLE_NAME = 'performance'
    _minstrel: int
    _page: int
    list_index: int
