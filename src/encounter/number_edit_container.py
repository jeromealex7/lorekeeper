from typing import Literal

from PySide2 import QtCore, QtWidgets

from src.widgets import NumberEdit


class NumberEditContainer(QtWidgets.QWidget):
    CHANGED = QtCore.Signal(float)

    def __init__(self, minimum: float | int = None, maximum: float | int = None, decimals: int = 0,
                 default: int | float = 0,  parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.number_edit = NumberEdit(minimum=minimum, maximum=maximum, decimals=decimals, default=default, parent=self)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.number_edit)
        self.setLayout(layout)
        self.number_edit.CHANGED.connect(self.CHANGED.emit)

    def get(self) -> int | float:
        return self.number_edit.get()

    def set(self, value: int | float | Literal['']):
        self.number_edit.set(value)
