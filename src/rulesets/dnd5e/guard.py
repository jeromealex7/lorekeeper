from src.model import Combatant, Guard as BasicGuard, Keep


class Guard(BasicGuard):
    name: str
    _treasure: int
    short_name: str
    gender: int                     # 0: neutral; 1: male; 2: female
    alignment: str                  # DropDown and Editable
    type: str                       # ENUM
    subtype: str                    # Editable
    size: str                       # ENUM
    challenge: str                  # ENUM
    languages: str                  # any
    hit_dice: str                   # RollWidget
    speed: str                      # str
    senses: str                     # str
    armor_class: str                # str
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    skills: str                     # str
    saves: str                      # str
    damage_vulnerabilities: str     # str
    damage_resistances: str         # str
    damage_immunities: str          # str
    condition_immunities: str       # str
    abilities: str                  # json: list[dict]
    traits: str

    @property
    def cha(self) -> int:
        return (self['charisma'] - 10) // 2

    @property
    def con(self) -> int:
        return (self['constitution'] - 10) // 2

    @property
    def cr(self) -> float | int:
        match self['challenge'].split('/'):
            case [numerator, denominator]:
                return int(numerator) / int(denominator)
            case [numerator]:
                return int(numerator or 0)

    @property
    def dex(self) -> int:
        return (self['dexterity'] - 10) // 2

    @property
    def finesse(self) -> int:
        return max(self.dex, self.str)

    @staticmethod
    def get_icon_name(type_: str) -> str:
        match type_.lower():
            case 'aberration': return 'ufo'
            case 'beast': return 'bear'
            case 'celestial': return 'angel'
            case 'construct': return 'robot'
            case 'dragon': return 'fire'
            case 'elemental': return 'drop'
            case 'fey': return 'sickle'
            case 'fiend': return 'devil'
            case 'giant': return 'person'
            case 'humanoid': return 'user'
            case 'monstrosity': return 'spider'
            case 'ooze': return 'object_ball'
            case 'plant': return 'leaf'
            case 'swarm': return 'worm'
            case 'undead': return 'skull'
            case _:
                return 'ballpen'

    @classmethod
    def new(cls, keep: Keep):
        guard = super().new(keep)
        guard['name'] = 'Unnamed Guard'
        guard['hit_dice'] = '2d8'
        guard['challenge'] = '1/8'
        guard['alignment'] = 'Unaligned'
        guard['size'] = 'Medium'
        guard['armor_class'] = '10'
        guard['subtype'] = 'any'
        guard['speed'] = '30 ft.'
        guard['strength'] = 10
        guard['dexterity'] = 10
        guard['constitution'] = 10
        guard['type'] = 'Humanoid'
        guard['intelligence'] = 10
        guard['wisdom'] = 10
        guard['charisma'] = 10
        guard['gender'] = 2
        return guard

    @property
    def prof(self) -> int:
        if self.cr < 1:
            return 2
        return 2 + (int(self.cr) - 1) // 4

    @property
    def str(self) -> int:
        return (self['strength'] - 10) // 2

    @property
    def wis(self) -> int:
        return (self['wisdom'] - 10) // 2

    def get_initiative_roll(self) -> str:
        return f'1d20{self.dex:+d}'

    def get_label(self) -> str:
        return f'{self["hit_dice"].split("d")[0]} HD'

    def get_maximum_hit_points_roll(self) -> str:
        try:
            count, die = self['hit_dice'].split('d')
            return f'{self["hit_dice"]}{int(count) * self.con:+d}'
        except ValueError:
            return self['hit_dice']

    def get_power(self):
        return f'CR {self["challenge"]}'

    def to_combatant(self) -> Combatant:
        return Combatant(keep=self.keep, data={'initiative_roll': f'1d20{self.dex:+d}', '_guard': self.db_index,
                                               'label': f'{self["hit_dice"].split("d")[0]} HD',
                                               'maximum_hit_points_roll': self.get_maximum_hit_points_roll(),
                                               'power': f'CR {self["challenge"]}', 'name': self['name']})

    # int is protected; implement last
    @property
    def int(self) -> int:
        return (self['intelligence'] - 10) // 2
