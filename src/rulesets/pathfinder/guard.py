from src.model import Combatant, Guard as BasicGuard, Keep


class Guard(BasicGuard):
    name: str
    short_name: str
    traits: str
    _treasure: int
    level: int
    gender: int
    size: str
    type: str
    languages: str
    info: str
    text: str
    strength: str
    dexterity: str
    constitution: str
    intelligence: str
    wisdom: str
    charisma: str
    armor_class: str
    fortitude: str
    reflex: str
    will: str
    saves: str
    hit_points: int
    hit_points_comment: str
    resistances: str
    weaknesses: str
    immunities: str
    perception: int
    senses: str
    skills: str
    items: str
    speed: str
    abilities: str

    @staticmethod
    def get_icon_name(type_: str) -> str:
        match type_.lower():
            case 'aberration': return 'ufo'
            case 'animal': return 'bear'
            case 'astral': return 'star2'
            case 'celestial': return 'angel'
            case 'construct': return 'robot'
            case 'dragon': return 'fire'
            case 'elemental': return 'drop'
            case 'ethereal': return 'planet'
            case 'fey': return 'sickle'
            case 'fiend': return 'devil'
            case 'fungus': return 'mushroom'
            case 'humanoid': return 'user'
            case 'monitor': return 'scales'
            case 'ooze': return 'object_ball'
            case 'plant': return 'leaf'
            case 'spirit': return 'ghost'
            case 'undead': return 'skull'
            case _: return 'ballpen'

    @classmethod
    def new(cls, keep: Keep):
        guard = cls(keep)
        guard['name'] = 'New Guard'
        guard['level'] = 0
        guard['type'] = 'Humanoid'
        guard['size'] = 'Medium'
        guard['perception'] = 5
        guard['strength'] = '+0'
        guard['dexterity'] = '+0'
        guard['constitution'] = '+0'
        guard['intelligence'] = '+0'
        guard['wisdom'] = '+0'
        guard['charisma'] = '+0'
        guard['armor_class'] = '15'
        guard['fortitude'] = '+5'
        guard['reflex'] = '+5'
        guard['will'] = '+5'
        guard['hit_points'] = 10
        guard['speed'] = '25 feet'
        return guard

    def to_combatant(self) -> Combatant:
        return Combatant(keep=self.keep, data={'initiative_roll': f'1d20{self["perception"]:+d}',
                                               '_guard': self.db_index,
                                               'label': f'Level {self["level"]}',
                                               'maximum_hit_points_roll': self["hit_points"],
                                               'power': f'level {self["level"]}', 'name': self['name']})
