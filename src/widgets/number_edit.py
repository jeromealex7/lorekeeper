from typing import Literal

from PySide2 import QtCore, QtWidgets

from .number_validator import NumberValidator


class NumberEdit(QtWidgets.QLineEdit):
    CHANGED = QtCore.Signal(float)

    def __init__(self, minimum: float | int = None, maximum: float | int = None, decimals: int = 0,
                 default: int | float = 0, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.default = default
        self.setMinimumWidth(60)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
        self._validator = NumberValidator(minimum=minimum, maximum=maximum, decimals=decimals, parent=self)
        self.setValidator(self._validator)

        self.textChanged.connect(self.on_text_change)
        self._validator.VALIDATION_CHANGED.connect(self.on_validation_changed)

    def get(self) -> float | int:
        try:
            if self._validator.decimals:
                return round(float(self.text()), self._validator.decimals)
            return int(float(self.text()))
        except ValueError:
            return self.default

    def on_text_change(self):
        if not self.hasAcceptableInput():
            return
        self.CHANGED.emit(self.get())

    def on_validation_changed(self, validated: bool):
        if validated:
            self.setStyleSheet('NumberEdit{background-color: white;};')
        else:
            self.setStyleSheet('NumberEdit{background-color: red;};')

    def set(self, value: int | float | Literal['']):
        if value == '':
            self.setText('')
            return
        if self._validator.maximum is not None:
            value = min(value, self._validator.maximum)
        if self._validator.minimum is not None:
            value = max(value, self._validator.minimum)
        if value == int(value):
            value = int(value)
        value = round(value, decimals) if (decimals := self._validator.decimals) else int(value)
        self.setText(str(value))

    def set_decimals(self, value: int):
        self._validator.decimals = value
        self._validator.validate(self.text(), 0)

    def set_maximum(self, value: int | float = None):
        self._validator.maximum = value
        self._validator.validate(self.text(), 0)

    def set_minimum(self, value: int | float = None):
        self._validator.minimum = value
        self._validator.validate(self.text(), 0)
