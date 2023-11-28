from PySide2 import QtWidgets

from src.model import Keep, Treasure
from src.widgets import BuildingToolbar


class TreasuryToolbar(BuildingToolbar):
    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(keep=keep, feature_type=Treasure, parent=parent)

    @staticmethod
    def get_icon_name(type_: str) -> str:
        return Treasure.get_icon_name(type_)
