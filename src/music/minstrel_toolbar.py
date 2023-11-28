from PySide2 import QtWidgets

from src.model import Keep, Minstrel
from src.widgets import BuildingToolbar


class MinstrelToolbar(BuildingToolbar):

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(keep=keep, feature_type=Minstrel, parent=parent)
