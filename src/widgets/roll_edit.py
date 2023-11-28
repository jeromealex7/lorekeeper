from PySide2 import QtCore, QtWidgets

from .roll_validator import RollValidator


class RollEdit(QtWidgets.QLineEdit):

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setMinimumWidth(80)
        self.roll_validator = RollValidator(self)
        self.setValidator(self.roll_validator)
        self.roll_validator.VALIDATION_CHANGED.connect(self.on_validation_changed)

    def get(self) -> str:
        return self.text().strip()

    def on_validation_changed(self, validated: bool):
        if validated:
            self.setStyleSheet('QLineEdit{background-color: white;};')
        else:
            self.setStyleSheet('QLineEdit{background-color: red;};')

    def set(self, value: int | float | str):
        self.setText(str(value))
