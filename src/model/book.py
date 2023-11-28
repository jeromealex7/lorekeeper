from PySide2.QtGui import QImage

from .feature import Feature
from .treasure import Treasure


class Book(Feature):
    TABLE_NAME = 'book'
    TAG_TABLE_NAME = 'keyword'
    name: str
    text: str
    keywords: str
    type: str
    _treasure: int

    def commit(self) -> int:
        self['keywords'] = ', '.join(self.get_tags())
        return super().commit()

    def get_html(self) -> str:
        return self['text']

    def get_plain_text(self) -> str:
        return self['text']

    def get_tags(self) -> list[str]:
        df = self.keep.buildings['keyword'].df
        return df[df['_book'] == self.db_index]['name'].values.tolist()

    @property
    def icon_name(self) -> str:
        return self['type']

    def to_image(self) -> QImage:
        try:
            return Treasure.read_keep(self.keep, self['_treasure']).to_image()
        except KeyError:
            return super().to_image()
