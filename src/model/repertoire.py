from .feature import Feature


class Repertoire(Feature):
    TABLE_NAME = 'repertoire'
    _minstrel: int
    _treasure: int
    list_index: int
