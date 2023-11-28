from datetime import datetime
from html.parser import HTMLParser
from typing import ClassVar, Literal, TypeVar

import pandas as pd
from PySide2.QtGui import QImage
from PySide2.QtCore import QByteArray, QMimeData

from src.settings import PATHS, SIGNALS

Keep = TypeVar('Keep')


class TextParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.body = False
        self.text = ''

    def handle_data(self, data: str):
        if self.body:
            self.text += data

    def handle_endtag(self, tag: str):
        if tag == 'body':
            self.body = False

    def handle_starttag(self, tag: str, _):
        if tag == 'body':
            self.body = True


class Feature(pd.Series):
    BYTE_SIZE: ClassVar[int] = 8
    ENDIANNESS: ClassVar[Literal['little', 'big']] = 'big'
    TABLE_NAME: ClassVar[str] = None
    TAG_TABLE_NAME: ClassVar[str] = None
    TIMESTAMP_FORMAT: ClassVar[str] = '%Y-%m-%d %H:%M:%S'

    def __init__(self, keep: Keep, db_index: int = 0, name: str = None, data: dict = None):
        super().__init__(name=name, data=self.get_default_data(data))
        self.building = keep.buildings[self.TABLE_NAME]
        self.df: pd.DataFrame = self.building.df
        self.db_index = db_index
        self.keep = keep

    def __bool__(self) -> bool:
        return True

    def commit(self) -> int:
        timestamp = self.get_time_stamp()
        self.db_index = self.db_index or self.get_new_index()
        self['_created'] = self['_created'] or timestamp
        self['_modified'] = timestamp
        self.df.loc[self.db_index] = pd.Series(data=self)
        self.building.is_modified = True
        SIGNALS.FEATURE_COMMIT.emit(self.TABLE_NAME, self.db_index)
        return self.db_index

    def delete(self):
        self.df.drop(self.db_index, axis='index', inplace=True)
        self.building.reset_columns()
        self.building.is_modified = True
        SIGNALS.FEATURE_DELETE.emit(self.TABLE_NAME, self.db_index)

    @classmethod
    def get_default_data(cls, data: dict = None) -> dict[str, str | int]:
        return {field_name: dtype() for field_name, dtype in cls.__annotations__.items()} | \
               {'_created': '', '_modified': ''} | (data or {})

    def get_html(self) -> str:
        return ''

    def get_new_index(self) -> int:
        indices = set(self.df.index.values)
        current = 1
        while current in indices:
            current += 1
        return current

    def get_plain_text(self) -> str:
        parser = TextParser()
        parser.feed(self.get_html())
        return parser.text.strip()

    def get_tags(self) -> list[str]:
        return []

    @classmethod
    def get_time_stamp(cls) -> str:
        return datetime.now().strftime(cls.TIMESTAMP_FORMAT)

    @property
    def icon_name(self) -> str:
        return ''

    @classmethod
    def new(cls, keep: Keep):
        return cls(keep=keep, db_index=0)

    @classmethod
    def read_keep(cls, keep: Keep, db_index: int | bytes):
        if isinstance(db_index, bytes):
            db_index = int.from_bytes(db_index, cls.ENDIANNESS)
        feature = cls(keep, db_index)
        feature.update(feature.df.loc[db_index].copy())
        return feature

    def reload(self):
        if not self.db_index:
            return
        copy = self.df.loc[self.db_index]
        self.update(copy)

    def to_bytes(self) -> bytes:
        return self.db_index.to_bytes(self.BYTE_SIZE, self.ENDIANNESS)

    def to_image(self) -> QImage:
        return QImage(PATHS['icons'].joinpath(self.icon_name).as_posix().__str__())

    def to_mime_data(self) -> QMimeData:
        mime_data = QMimeData()
        mime_data.setData(f'lorekeeper/{self.TABLE_NAME}', QByteArray(self.to_bytes()))
        return mime_data
