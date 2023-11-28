from .feature import Feature


class Inscription(Feature):
    TABLE_NAME = 'inscription'
    name: str
    _treasure: int
