from PySide2 import QtCore, QtGui, QtWidgets

from src.widgets import TokenSelector


class TokenWidget(QtWidgets.QWidget):
    CHANGED = QtCore.Signal(str)
    SIZE: int = 40

    def __init__(self, value: str = '', parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.button = QtWidgets.QToolButton(self)
        self.button.setIconSize(QtCore.QSize(self.SIZE, self.SIZE))
        self.button.clicked.connect(self.on_click)
        self.token = value

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.button)
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)

        self.set(value)

    def get(self) -> str:
        return self.token

    def on_click(self):
        selector = TokenSelector(default=self.get(), parent=self)
        selector.exec_()
        if not selector.icon_path:
            return
        self.set(selector.icon_path)

    def set(self, value: str):
        value = value or ''
        self.token = value
        self.button.setIcon(QtGui.QIcon(value))
        self.CHANGED.emit(value)
