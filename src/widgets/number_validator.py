import re

from PySide2 import QtCore, QtGui, QtWidgets


class NumberValidator(QtGui.QValidator):
    REGEX = re.compile(r'^\s*(?:-\s*)?\d*(?:\.\d*)?$')
    VALIDATION_CHANGED = QtCore.Signal(bool)

    def __init__(self, minimum: float | int = None, maximum: float | int = None, decimals: int = 0,
                 parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.minimum = minimum
        self.maximum = maximum
        self.decimals = decimals

    def validate(self, text: str, pos: int) -> QtGui.QValidator.State:
        if not re.match(fr'^\s*(?:-\s*)?\d*(?:\.\d{{0,{self.decimals}}})?$', text) or \
                self.minimum and self.minimum >= 0 and '-' in text or not self.decimals and '.' in text:
            return QtGui.QValidator.Invalid
        try:
            value = float(text or 0)
            if value != round(value, self.decimals):
                raise ValueError
            if self.minimum is not None and value < self.minimum or \
               self.maximum is not None and value > self.maximum:
                raise ValueError
        except ValueError:
            self.VALIDATION_CHANGED.emit(False)
            return QtGui.QValidator.Intermediate
        self.VALIDATION_CHANGED.emit(True)
        return QtGui.QValidator.Acceptable
