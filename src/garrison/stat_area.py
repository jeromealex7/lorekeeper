from PySide2 import QtCore, QtWidgets

from src.model import Guard
from src.rulesets import RULESET


class StatArea(QtWidgets.QScrollArea):

    def __init__(self, guard: Guard, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.guard = guard
        self.stat_block = RULESET.get_stat_block(guard)
        self.setWidget(self.stat_block)
        self.setWidgetResizable(True)
        self.stat_block.installEventFilter(self)
        self.stat_block.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.stat_block.setContentsMargins(0, 0, 0, 0)
        self.resize(self.stat_block.size())
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def fit(self):
        width, height = self.stat_block.size().toTuple()
        self.resize(2 + width, min(2 + height, int(.95 * self.screen().size().height())))
