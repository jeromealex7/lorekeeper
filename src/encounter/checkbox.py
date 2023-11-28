from PySide2 import QtCore, QtWidgets

from src.widgets import Icon


class Checkbox(QtWidgets.QWidget):
    CHANGED = QtCore.Signal(bool)
    SIZE: int = 40

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.button = QtWidgets.QToolButton(self)
        self.button.setIcon(Icon('eye'))
        self.button.setIconSize(QtCore.QSize(self.SIZE, self.SIZE))
        self.button.setCheckable(True)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.button)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.button.toggled.connect(self.CHANGED.emit)

    def get(self) -> bool:
        return self.button.isChecked()

    def set(self, value: bool):
        self.button.setChecked(value)
