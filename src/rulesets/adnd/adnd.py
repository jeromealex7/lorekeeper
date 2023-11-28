from PySide2 import QtWidgets

from .constants import MONSTER_TABLE
from .guard import Guard
from .guard_inspector import GuardInspector
from .stat_block import StatBlock
from .encounter_gage import EncounterGage
from src.rulesets.ruleset import Ruleset


class ADnD(Ruleset):
    GARRISON_HEADER = (('name', 'Name'), *(tuple(reversed(e)) for e in MONSTER_TABLE), ('_modified', 'Last Modified'),
                       ('_created', 'Created'), ('traits', 'Traits'))
    GUARD_TYPE = Guard
    GUARD_INSPECTOR = GuardInspector
    INITIATIVE_ASCENDING = False
    POWER_LEVELS = 'int'
    PLAYER_LEVELS = tuple((f'level {level}', level) for level in range(1, 21))

    def get_encounter_gage(self, parent: QtWidgets.QWidget | None = None) -> EncounterGage:
        return EncounterGage(keep=self.keep, parent=parent)

    def get_stat_block(self, guard: Guard, parent: QtWidgets.QWidget | None = None) -> StatBlock:
        return StatBlock(guard=guard, parent=parent)
