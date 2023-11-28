from .feature import Feature


class Genre(Feature):
    TABLE_NAME = 'genre'
    _minstrel: int
    name: str
