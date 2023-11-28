from src.model import Combatant, Guard as BasicGuard, Keep


class Guard(BasicGuard):
    name: str
    _treasure: int
    type: str
    climate: str
    frequency: str
    organization: str
    activity: str
    diet: str
    intelligence: str
    treasure: str
    alignment: str
    appearing: str
    armor_class: str
    movement: str
    hit_dice: str
    thac0: str
    attacks: str
    damage: str
    offensive: str
    defensive: str
    magic_resistance: str
    size: str
    morale: str
    xp: str
    text: str

    @staticmethod
    def get_icon_name(type_: str) -> str:
        return 'skull'

    def get_initiative_roll(self) -> str:
        return f'1d20{self.dex:+d}'

    def get_label(self) -> str:
        return f'{self["hit_dice"].split("d")[0]} HD'

    def get_maximum_hit_points_roll(self) -> str:
        try:
            count_str, *additional = self['hit_dice'].split('+')
            count = int(count_str.strip())
            modifier = int(additional[0]) if additional else 0
            return f'{count}d8+{modifier}'
        except ValueError:
            return self['hit_dice']

    def get_power(self) -> str:
        return f'CR {self["challenge"]}'

    def get_size(self) -> int:
        match self['size'].split(' ')[0]:
            case 'T': return 1
            case 'S': return 2
            case 'M': return 3
            case 'L': return 4
            case 'G': return 5
            case _: return 6

    def get_xp(self) -> int:
        try:
            return int(self['xp'].replace(',', '').strip())
        except ValueError:
            return 0

    @classmethod
    def new(cls, keep: Keep):
        raise NotImplementedError('AD&D guards cannot not be newly created.')

    def to_combatant(self) -> Combatant:
        return Combatant(keep=self.keep, data={'initiative_roll': self.get_size(), '_guard': self.db_index,
                                               'label': f'HD {self["hit_dice"]}; AC {self["armor_class"]}',
                                               'maximum_hit_points_roll': self.get_maximum_hit_points_roll(),
                                               'power': self.get_xp(), 'name': self['name']})
