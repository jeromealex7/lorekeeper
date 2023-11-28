from PySide2 import QtWidgets

from src.model import Encounter, Keep
from src.widgets import BuildingToolbar


class EncounterToolbar(BuildingToolbar):

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(keep=keep, feature_type=Encounter, parent=parent)
