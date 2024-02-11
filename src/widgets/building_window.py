from typing import Literal

from PySide2 import QtGui, QtWidgets


class BuildingWindow(QtWidgets.QMainWindow):

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet('*{font-family: Roboto Slab; font-size: 10pt;};')
        self.full_screen = QtWidgets.QShortcut(QtGui.QKeySequence('Alt+Return'), self)
        self.full_screen.activated.connect(self.on_full_screen)

    def closeEvent(self, event: QtGui.QCloseEvent):
        self.hide()
        event.ignore()

    def on_full_screen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def set_visibility(self, state: bool | Literal['toggle'] = True):
        state = self.isHidden() if state == 'toggle' else state
        if state:
            self.showNormal()
            self.setFocus()
            self.activateWindow()
            self.raise_()
        else:
            self.hide()
