from functools import partial
from typing import Callable

from PySide2 import QtCore, QtGui, QtWidgets


class ShortcutManager(QtCore.QObject):

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._shortcuts: dict[str, Callable[[QtWidgets.QMainWindow], None]] = {}

    def activate_shortcuts(self, parent: QtWidgets.QMainWindow):
        for key_sequence, func in self._shortcuts.items():
            shortcut = QtWidgets.QShortcut(parent)
            shortcut.setKey(QtGui.QKeySequence(key_sequence))
            shortcut.activated.connect(partial(func, parent))

    def create_shortcut(self, key_sequence: str, func: Callable[[QtWidgets.QMainWindow], None]):
        self._shortcuts[key_sequence] = func


SHORTCUTS = ShortcutManager()
