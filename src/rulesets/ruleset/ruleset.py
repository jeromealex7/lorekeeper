from typing import ClassVar, Literal, Type

from PySide2 import QtWidgets

from .encounter_gage import EncounterGage
from .stat_block import StatBlock
from src.model import Guard, Keep


class Ruleset:
    GARRISON_HEADER: tuple[tuple[str, str], ...] = ()
    GUARD_TYPE: Type[Guard] = Guard
    GUARD_INSPECTOR: Type[QtWidgets.QWidget] = QtWidgets.QWidget
    HIT_POINTS_CRITICAL: ClassVar[int] = 0
    HIT_POINTS_MINIMUM: ClassVar[int] = 0
    INITIATIVE_ASCENDING: ClassVar[bool] = False
    PLAYER_LEVELS: ClassVar[Literal['int', 'str'] | tuple[tuple[str, int], ...]] = 'str'
    POWER_LEVELS: ClassVar[tuple[str, ...]] = ()

    def __init__(self, keep: Keep = None):
        self.keep = keep

    def get_encounter_gage(self, parent: QtWidgets.QWidget | None = None) -> EncounterGage:
        raise NotImplementedError

    def get_stat_block(self, guard: Guard, parent: QtWidgets.QWidget | None = None) -> StatBlock:
        raise NotImplementedError
