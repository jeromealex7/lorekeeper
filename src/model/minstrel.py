from typing import TypeVar

from .feature import Feature
Keep = TypeVar('Keep')


class Minstrel(Feature):
    TABLE_NAME = 'minstrel'
    TAG_TABLE_NAME = 'genre'
    name: str
    genres: str
    state: int
    count: int

    def commit(self) -> int:
        self['genres'] = ', '.join(self.get_tags())
        return super().commit()

    def get_tags(self) -> list[str]:
        df = self.keep.buildings['genre'].df
        return df[df['_minstrel'] == self.db_index]['name'].values.tolist()

    def get_treasures(self) -> list[int]:
        df = self.keep.buildings['repertoire'].df.sort_values(by='list_index')
        return df[df['_minstrel'] == self.db_index]['_treasure'].values.tolist()

    @property
    def icon_name(self) -> str:
        return 'clef'

    @classmethod
    def read_string(cls, keep: Keep, string: str):
        minstrel = Minstrel.new(keep=keep)
        minstrel['name'] = string
        return minstrel
