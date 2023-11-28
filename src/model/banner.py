from .feature import Feature


class Banner(Feature):
    TABLE_NAME = 'banner'
    name: str
    _encounter: int
