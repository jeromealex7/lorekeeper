import pandas as pd

from src.rulesets import EncounterGage as BasicEncounterGage


class EncounterGage(BasicEncounterGage):

    def set_encounter_data(self, data: pd.DataFrame):

        def get_xp(series: pd.Series) -> int:
            if series['type'] == 'player':
                return 0
            try:
                type_, level = series['power'].split(' ', 1)
            except ValueError:
                return 0
            match int(level) - self.keep.player_level:
                case x if x < -4: xp = 0
                case -4: xp = 10
                case -3: xp = 15
                case -2: xp = 20
                case -1: xp = 30
                case 0: xp = 40
                case 1: xp = 60
                case 2: xp = 80
                case 3: xp = 120
                case 4: xp = 160
                case _: xp = 1000
            if type_ == 'simple':
                xp //= 5
            return xp
        if data is None or data.empty:
            total_xp = 0
        else:
            total_xp = data.apply(get_xp, axis=1).sum()
        adjusted_xp = total_xp / (1 + (self.keep.player_count - 4) / 4)
        if adjusted_xp <= 40:
            difficulty = 'trivial'
        elif adjusted_xp <= 60:
            difficulty = 'low'
        elif adjusted_xp <= 80:
            difficulty = 'moderate'
        elif adjusted_xp <= 120:
            difficulty = 'severe'
        elif adjusted_xp <= 160:
            difficulty = 'extreme'
        else:
            difficulty = 'impossible'
        red = int(200 * min(adjusted_xp / 80, 1))
        green = int(200 * max(min(2 - adjusted_xp / 80, 1), 0))
        blue = 0
        self.setStyleSheet(f'EncounterGage{{background-color: rgb({red},{green},{blue});'
                           f'font-family: Roboto Slab;font-size: 20pt;padding: 5px}}')
        if adjusted_xp > 160:
            self.setText(difficulty)
        else:
            self.setText(f'{difficulty}\n({total_xp} XP)')

