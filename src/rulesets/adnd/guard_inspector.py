from PySide2 import QtCore, QtGui, QtWidgets

from .stat_block import StatBlock
from src.model import Guard
from src.settings import SHORTCUTS
from src.widgets import Icon


class GuardInspector(QtWidgets.QMainWindow):

    def __init__(self, guard: Guard, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowMinimizeButtonHint &
                            ~QtCore.Qt.WindowMaximizeButtonHint)
        SHORTCUTS.activate_shortcuts(self)
        self.guard = guard
        self.stat_block = StatBlock(guard, self)
        self.setCentralWidget(self.stat_block)
        self.setWindowIcon(Icon('skull'))
        self.setWindowTitle(guard['name'])
