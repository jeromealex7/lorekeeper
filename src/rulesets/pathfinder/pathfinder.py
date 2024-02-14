from PySide2 import QtWidgets

from .encounter_gage import EncounterGage
from .guard import Guard
from .guard_inspector import GuardInspector
from .stat_block import StatBlock
from src.rulesets.ruleset import Ruleset


class Pathfinder(Ruleset):
    GARRISON_HEADER = (('name', 'Name'), ('type', 'Type'), ('level', 'Level'), ('perception', 'Perception'),
                       ('senses', 'Senses'), ('languages', 'Languages'), ('skills', 'Skills'), ('strength', 'Str'),
                       ('dexterity', 'Dex'), ('constitution', 'Con'),  ('intelligence', 'Int'), ('wisdom', 'Wis'),
                       ('charisma', 'Cha'), ('items', 'Items'), ('armor_class', 'AC'), ('fortitude', 'Fort'),
                       ('reflex', 'Ref'), ('will', 'Will'), ('saves', 'Saves'), ('resistances', 'Resistances'),
                       ('immunities', 'Immunities'), ('weaknesses', 'Weaknesses'), ('speed', 'Speed'),
                       ('hit_points', 'HP'), ('hit_points_comment', 'HP Comment'), ('_modified', 'Last Modified'),
                       ('_created', 'Created'), ('traits', 'Traits'))

    GUARD_INSPECTOR = GuardInspector
    GUARD_TYPE = Guard
    POWER_LEVELS = ('', *(f'level {level}' for level in range(-2, 22)), *(f'simple {level}' for level in range(-1, 21)))
    PLAYER_LEVELS = tuple((f'level {level}', level) for level in range(1, 21))

    def get_encounter_gage(self, parent: QtWidgets.QWidget | None = None) -> EncounterGage:
        return EncounterGage(keep=self.keep, parent=parent)

    def get_stat_block(self, guard: Guard, parent: QtWidgets.QWidget | None = None) -> StatBlock:
        return StatBlock(guard=guard, parent=parent)
