from PySide2 import QtWidgets

from src.model import Keep
from src.rulesets import RULESET
from src.widgets import BuildingToolbar


class GuardToolbar(BuildingToolbar):

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(keep=keep, feature_type=RULESET.GUARD_TYPE, parent=parent)

    @staticmethod
    def get_icon_name(type_: str) -> str:
        return RULESET.GUARD_TYPE.get_icon_name(type_)
