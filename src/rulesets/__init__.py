from typing import TypeVar

from src.model import Building
from .ruleset import EncounterGage, Ruleset
_RULESET = None
Keep = TypeVar('Keep')


def load_ruleset(ruleset_name: str, keep: Keep):
    global _RULESET
    match ruleset_name:
        case 'pathfinder':
            from .pathfinder import Pathfinder
            _RULESET = Pathfinder(keep=keep)
        case 'dnd':
            from .dnd5e import Dnd5e
            _RULESET = Dnd5e(keep=keep)
        case 'adnd':
            from .adnd import ADnD
            _RULESET = ADnD(keep=keep)
    b = Building.read_keep(keep, _RULESET.GUARD_TYPE)
    keep.buildings['guard'] = b


class RulesetManager:

    def __getattribute__(self, name: str):
        return getattr(_RULESET, name)


RULESET = RulesetManager()
