import io
import os
from pathlib import Path
import re
import shutil
from typing import TypeVar
import uuid

import pandas as pd
from PySide2.QtCore import QBuffer, QByteArray, QMimeData, QUrl
from PySide2.QtGui import QImage
import requests

from .feature import Feature
from src.settings import PATHS
Keep = TypeVar('Keep')


class Treasure(Feature):
    IMAGE_FORMATS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.svg', '.gif')
    MUSIC_FORMATS = ('.mp3', '.wav', '.avi', '.mp4', '.m4a', '.webm')
    WORD_FORMATS = ('.doc', '.docx', '.docm')
    EXCEL_FORMATS = ('.xls', '.xlsx', '.xlsm')

    REGEX_YOUTUBE = re.compile(r'^((?:https?:)?//)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))'
                               r'(/(?:[\w\-]+\?v=|embed/|live/|v/)?)([\w\-]+)(\S+)?$')
    TABLE_NAME = 'treasure'
    TAG_TABLE_NAME = 'inscription'
    info: str
    inscriptions: str   # set in self.commit
    name: str
    size: int           # set in self.localize
    suffix: str
    text: str
    type: str
    uuid: str           # set in self.localize

    def __init__(self, keep: Keep, db_index: int = 0, data: dict = None):
        super().__init__(keep=keep, db_index=db_index, data=data, )
        self._bytes = b''

    @property
    def bytes(self):
        return self._bytes or self.path.read_bytes()

    def commit(self) -> int:
        self['text'] = self['text'].strip()
        self['inscriptions'] = ', '.join(self.get_tags())
        self.localize(False)
        return super().commit()

    def find_usage(self) -> str:
        buildings = self.keep.buildings
        thumbnails = (df := buildings['book'].df)[df['_treasure'] == self.db_index]['name'].values.tolist()
        guards = (df := buildings['guard'].df)[df['_treasure'] == self.db_index]['name'].values.tolist()
        books = pd.read_sql(f'''SELECT
                                t.name 'treasure_name',
                                b.name 'book_name',
                                p.name 'page_name'
                                FROM
                                treasure t
                                INNER JOIN chart c ON c._treasure = t._index
                                INNER JOIN page p ON p._index = c._page
                                INNER JOIN book b ON b._index = p._book
                                AND t._index = {self.db_index}''', self.keep.connection)
        minstrels = pd.read_sql(f'''SELECT t.name 'treasure_name',
                                    m.name 'minstrel_name'
                                    FROM treasure t
                                    INNER JOIN repertoire r ON t._index = r._treasure
                                    INNER JOIN minstrel m ON r._minstrel = m._index
                                    WHERE t._index = {self.db_index}''', self.keep.connection)
        results = []
        if self.keep.treasure_index == self.db_index:
            results.append('The Treasure is used as the thumbnail for this Keep.')
        if thumbnails:
            results.append('The Treasure is used as the thumbnail for the following books:\n' +
                           '\n'.join(f'• {thumbnail}' for thumbnail in thumbnails))
        if guards:
            results.append('The Treasure is used as the image for the following guards:\n' +
                           '\n'.join(f'• {guard}' for guard in guards))
        if not books.empty:
            def _add_reference(series: pd.Series):
                return f'• {series["book_name"]} (p. {series["page_name"]})'
            results.append('The Treasure is referenced in the following books:\n' +
                           '\n'.join(books.apply(_add_reference, axis=1).values.tolist()))
        if not minstrels.empty:
            def _add_reference(series: pd.Series):
                return f'• {series["minstrel_name"]}'
            results.append('The Treasure is performed by the following minstrels:\n' +
                           '\n'.join(minstrels.apply(_add_reference, axis=1).values.tolist()))
        return '\n\n'.join(results)

    def get_html(self) -> str:
        return self['text']

    @staticmethod
    def get_icon_name(type_: str) -> str:
        match type_:
            case 'url': return 'earth_link'
            case 'youtube': return 'earth_music'
            case 'music': return 'music'
            case 'image': return 'photo_landscape'
            case 'word': return 'word'
            case 'excel': return 'excel'
            case 'pdf': return 'pdf'
            case 'python': return 'code'
            case _: return 'document_empty'

    def get_tags(self) -> list[str]:
        df = self.keep.buildings['inscription'].df
        return df[df['_treasure'] == self.db_index]['name'].values.tolist()

    @classmethod
    def get_uuid_from_bytes(cls, b: bytes) -> str:
        return uuid.uuid5(uuid.NAMESPACE_URL, b.hex()).hex

    @property
    def icon_name(self) -> str:
        return self.get_icon_name(self['type'])

    def localize(self, overwrite: bool = False):
        if ':' in self['suffix']:
            return
        self['uuid'] = self.uuid
        if not self.path.exists() or overwrite:
            self.path.write_bytes(self.bytes)
        self['size'] = self.path.stat().st_size

    @property
    def path(self) -> Path:
        return PATHS['inventory'].joinpath(self.uuid)

    @classmethod
    def read_drag_data(cls, keep: Keep, data: QMimeData) -> list:
        if data.hasUrls():
            mimes = []
            for url in data.urls().copy():
                new_data = QMimeData()
                new_data.setUrls([url])
                mimes.append(new_data)
            return [cls.read_mime_data(keep, mime) for mime in mimes]
        return [cls.read_mime_data(keep, data)]

    @classmethod
    def read_mime_data(cls, keep: Keep, data: QMimeData):
        if data.hasFormat('lorekeeper/treasure'):
            try:
                return cls.read_keep(keep, data.data('lorekeeper/treasure').data())
            except KeyError:
                pass
        if data.hasUrls():
            url = data.urls()[0]
        elif data.hasText():
            url = QUrl(data.text())
        else:
            url = None
        if url:
            if (path := Path(url.toLocalFile())).exists() and path.is_file():
                return cls.read_path(keep, path)
            if url.isValid() and url.scheme() and url.host():
                url_image = cls.read_url(keep, url.url())
                if url_image:
                    return url_image
                treasure = cls.new(keep)
                treasure['name'] = url.fileName()
                treasure['info'] = url.url()
                treasure['suffix'] = 'URL:youtube' if cls.REGEX_YOUTUBE.match(url.url()) else 'URL:other'
                treasure['type'] = treasure.type_
                return treasure
        if data.hasImage() and not (image := QImage(data.imageData())).isNull():
            treasure = cls.new(keep)
            treasure['name'] = 'Image'
            treasure['info'] = f'PNG Image: {"x".join(map(str, image.size().toTuple()))}'
            treasure['suffix'] = '.png'
            treasure['type'] = treasure.type_
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            image.save(buffer, 'PNG')
            treasure.set_bytes(byte_array.data())
            return treasure
        return None

    @classmethod
    def read_path(cls, keep: Keep, path: str | os.PathLike[str]):
        path = Path(path)
        if not path.exists() or not path.is_file():
            return None
        treasure = cls.new(keep)
        treasure['name'] = path.stem
        treasure['suffix'] = path.suffix.lower()
        treasure['type'] = treasure.type_
        if treasure['type'] == 'image':
            image = QImage(path.as_posix().__str__())
            if image.isNull():
                return None
            treasure['info'] = f'PNG Image: {"x".join(map(str, image.size().toTuple()))}'
        else:
            treasure['info'] = 'Local File'
        treasure.set_bytes(path.read_bytes())
        return treasure

    @classmethod
    def read_url(cls, keep: Keep, url: str, silent: bool = True):
        suffix = Path(url).suffix.lower()
        if suffix not in cls.IMAGE_FORMATS:
            return None
        try:
            with requests.get(url, stream=True) as answer:
                with io.BytesIO() as content:
                    treasure = Treasure.new(keep)
                    shutil.copyfileobj(answer.raw, content)
                    treasure.set_bytes(content.getvalue())
                    treasure['type'] = 'image'
                    treasure['suffix'] = suffix
                    treasure['name'] = url.rsplit('/', 1)[-1]
                    treasure['info'] = url
                    return treasure
        except Exception as err:
            if silent:
                return None
            raise err

    def set_bytes(self, b: bytes):
        self._bytes = b

    def to_image(self) -> QImage:
        if self['type'] == 'image':
            return QImage.fromData(QByteArray(self.bytes))
        return QImage(PATHS['icons'].joinpath(self.icon_name).as_posix().__str__())

    @property
    def type_(self) -> str:
        match self['suffix']:
            case 'URL:other': return 'url'
            case 'URL:youtube': return 'youtube'
            case s if s.lower() in self.MUSIC_FORMATS: return 'music'
            case s if s.lower() in self.IMAGE_FORMATS: return 'image'
            case s if s.lower() in self.WORD_FORMATS: return 'word'
            case s if s.lower() in self.EXCEL_FORMATS: return 'excel'
            case '.pdf': return 'pdf'
            case '.py': return 'python'
            case _: return 'other'

    @property
    def uuid(self) -> str:
        return self['uuid'] or self.get_uuid_from_bytes(self._bytes)
