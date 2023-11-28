import io

import pandas as pd
from PySide2 import QtWidgets

from .constants import CHALLENGES
from .encounter_gage import EncounterGage
from .guard import Guard
from .guard_inspector import GuardInspector
from .stat_block import StatBlock
from src.model import Keep
from src.rulesets.ruleset import Ruleset


class Dnd5e(Ruleset):
    GARRISON_HEADER = (('name', 'Name'), ('type', 'Type'), ('subtype', 'Subtype'), ('challenge', 'Challenge'),
                       ('hit_dice', 'Hit Dice'), ('speed', 'Speed'), ('senses', 'Senses'), ('armor_class', 'Armor'),
                       ('strength', 'STR'), ('dexterity', 'DEX'), ('constitution', 'CON'), ('intelligence', 'INT'),
                       ('wisdom', 'WIS'), ('charisma', 'CHA'), ('saves', 'Saves'), ('skills', 'Skills'),
                       ('damage_vulnerabilities', 'Vulnerabilities'), ('damage_resistances', 'Resistances'),
                       ('damage_immunities', 'Damage Immunities'), ('condition_immunities', 'Condition Immunities'),
                       ('languages', 'Languages'), ('alignment', 'Alignment'), ('_modified', 'Last Modified'),
                       ('_created', 'Created'), ('traits', 'Traits'))
    GUARD_TYPE = Guard
    GUARD_INSPECTOR = GuardInspector
    POWER_LEVELS = ('', 'CR 1/8', 'CR 1/4', 'CR 1/2', *(f'CR {level}' for level in range(1, 21)))
    PLAYER_LEVELS = tuple((f'level {level}', level) for level in range(1, 21))

    def __init__(self, keep: Keep):
        super().__init__(keep=keep)
        df = pd.read_csv(io.StringIO(CHALLENGES), delimiter=';')
        df.set_index('level', drop=True, inplace=True)

        def calc(value) -> float:
            match value:
                case '-': return 100
                case 0: return 0
                case quotient:
                    try:
                        numerator, denominator = quotient.split(':')
                        return int(numerator) / int(denominator)
                    except ValueError:
                        return 100
        self.challenge_df = df.map(calc)

    def get_encounter_gage(self, parent: QtWidgets.QWidget | None = None) -> EncounterGage:
        return EncounterGage(keep=self.keep, parent=parent, challenge_df=self.challenge_df)

    def get_stat_block(self, guard: Guard, parent: QtWidgets.QWidget | None = None) -> StatBlock:
        return StatBlock(guard=guard, parent=parent)
