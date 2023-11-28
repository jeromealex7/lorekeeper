import pandas as pd
from PySide2 import QtCore, QtGui, QtWidgets

from src.model import Encounter, Keep


class EncounterGage(QtWidgets.QLabel):

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.keep = keep
        self.setFixedSize(200, 200)
        self.setAlignment(QtCore.Qt.AlignCenter)

    def preview(self, encounter: Encounter) -> QtGui.QPixmap:
        pixmap = QtGui.QPixmap(200, 200)
        self.set_encounter_data(encounter.get_combatant_frame())
        self.render(pixmap)
        return pixmap

    def set_encounter_data(self, data: pd.DataFrame):
        raise NotImplementedError
