from typing import Literal

from PySide2 import QtCore, QtWidgets

from src.widgets import Icon


class TypeSelector(QtWidgets.QWidget):
    CHANGED = QtCore.Signal(str)
    SIZE: int = 40

    def __init__(self, value: Literal['enemy', 'player', 'effect'] = 'enemy', parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.list = QtWidgets.QComboBox()
        self.list.addItem(Icon('user'), 'player', 'player')
        self.list.addItem(Icon('skull'), 'enemy', 'enemy')
        self.list.addItem(Icon('magic_wand'), 'effect', 'effect')
        self.list.setIconSize(QtCore.QSize(self.SIZE, self.SIZE))

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.list)
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        self.set(value)

        self.list.currentIndexChanged[str].connect(self.CHANGED.emit)

    def get(self) -> str:
        return self.list.currentData(QtCore.Qt.UserRole)

    def set(self, value: str):
        self.list.setCurrentText(str(value))
