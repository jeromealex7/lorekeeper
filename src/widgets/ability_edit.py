from PySide2 import QtWidgets

from .ability_highlighter import AbilityHighlighter
from src.model import Guard


class AbilityEdit(QtWidgets.QTextEdit):

    def __init__(self, guard: Guard, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.guard = guard
        self.keep = guard.keep
        self.highlighter = AbilityHighlighter(self.document(), guard.get_properties())
