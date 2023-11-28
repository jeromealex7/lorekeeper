from .feature import Feature


class Trait(Feature):
    TABLE_NAME = 'trait'
    _guard: int
    name: str
