import pandas as pd
from PySide2 import QtWidgets

from .constants import XP_TABLE
from src.model import Keep
from src.rulesets import EncounterGage as BasicEncounterGage


class EncounterGage(BasicEncounterGage):

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None, challenge_df: pd.DataFrame = None):
        super().__init__(keep=keep, parent=parent)
        self.challenge_df = challenge_df

    def set_encounter_data(self, data: pd.DataFrame):

        def get_difficulty(series: pd.Series) -> list[float]:
            if series['type'] == 'player':
                return [0, 0]
            try:
                _, cr = series['power'].split(' ', 1)
            except ValueError:
                return [0, 0]
            return [self.challenge_df.at[self.keep.player_level, cr], XP_TABLE.get(cr, 0)]
        if data is None or data.empty:
            difficulty, total_xp = [0, 0]
        else:
            difficulty, total_xp = data.apply(get_difficulty, axis=1, result_type='expand').sum(axis=0).tolist()
        difficulty /= self.keep.player_count
        red = int(200 * min(difficulty, 1))
        green = int(200 * max(min(2 - difficulty, 1), 0))
        blue = 0
        self.setStyleSheet(f'EncounterGage{{background-color: rgb({red},{green},{blue});'
                           f'font-family: Roboto Slab;font-size: 20pt;padding: 5px}}')
        if difficulty >= 100:
            self.setText('impossible')
        else:
            self.setText(f'{difficulty:.0%}\n({int(total_xp)} XP)')
