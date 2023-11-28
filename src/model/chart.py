from .feature import Feature


class Chart(Feature):
    TABLE_NAME = 'chart'
    _treasure: int
    _page: int
    list_index: int
