import pandas as pd

from .feature import Feature


class Encounter(Feature):
    TABLE_NAME = 'encounter'
    TAG_TABLE_NAME = 'banner'
    name: str
    text: str
    banners: str        # set in commit
    combatants: str     # set in commit

    def commit(self) -> int:
        self['banners'] = ', '.join(self.get_tags())
        return super().commit()

    def get_combatant_frame(self) -> pd.DataFrame:
        df = self.keep.buildings['combatant'].df
        return df[df['_encounter'] == self.db_index]

    def get_html(self) -> str:
        return self['text'] or f'<i>{self["combatants"]}</i>'

    def get_plain_text(self) -> str:
        return self['text'] or self['combatants']

    def get_tags(self) -> list[str]:
        df = self.keep.buildings['banner'].df
        return df[df['_encounter'] == self.db_index]['name'].values.tolist()

    @property
    def icon_name(self) -> str:
        return 'sword'
