import re

from PySide2 import QtCore, QtGui


class RollValidator(QtGui.QValidator):
    REGEX = re.compile(r'^(?:\s*[+-]?\s*\d+\s*(?:d\s*\d+|\.\d{1,3})?)*$')
    VALIDATION_CHANGED = QtCore.Signal(bool)

    def validate(self, text: str, pos: int) -> QtGui.QValidator.State:
        if any(not char.isnumeric() and char not in ' +-d.' for char in text):
            return QtGui.QValidator.Invalid
        if self.REGEX.match(text.replace(' ', '')):
            self.VALIDATION_CHANGED.emit(True)
            return QtGui.QValidator.Acceptable
        self.VALIDATION_CHANGED.emit(False)
        return QtGui.QValidator.Intermediate
