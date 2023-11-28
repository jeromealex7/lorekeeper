import pandas as pd

from src.rulesets import EncounterGage as BasicEncounterGage


class EncounterGage(BasicEncounterGage):

    def set_encounter_data(self, data: pd.DataFrame):

        def get_xp(series: pd.Series) -> int:
            if series['type'] == 'player':
                return 0
            try:
                return int(series['power'])
            except ValueError:
                return 0
        if data is None or data.empty:
            xp = 0
        else:
            xp = data.apply(get_xp, axis=1).sum(axis=0)
        self.setStyleSheet(f'EncounterGage{{background-color: rgb({100},{255},{100});'
                           f'font-family: Roboto Slab;font-size: 20pt;padding: 5px}}')
        self.setText(f'Total {xp} XP')
