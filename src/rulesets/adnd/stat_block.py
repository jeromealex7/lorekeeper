from PySide2 import QtWidgets

from .constants import MONSTER_TABLE
from .guard import Guard
from src.rulesets.ruleset import StatBlock as BasicStatBlock


class StatBlock(BasicStatBlock):

    def __init__(self, guard: Guard, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.guard = guard
        self.keep = guard.keep
        self.setStyleSheet('*{font-size: 8pt; background-color: white; font-family: Roboto Slab};')
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(600)
        self.resize(600, 800)
        self._layout = QtWidgets.QVBoxLayout()
        self.setLayout(self._layout)
        self.reload_guard()

    def reload_guard(self):
        self.clear()
        title = QtWidgets.QLabel(self.guard['name'])
        title.setStyleSheet('QLabel{font-size: 20pt;font-weight: bold;};')
        self._layout.addWidget(title, stretch=0)
        table = QtWidgets.QGridLayout()
        table.setColumnStretch(0, 0)
        table.setColumnStretch(1, 1)
        table.setSpacing(0)
        for row, (title, key) in enumerate(MONSTER_TABLE):
            label = QtWidgets.QLabel(title + ':')
            label.setStyleSheet('QLabel{font-weight: bold;};')
            value = QtWidgets.QLabel(self.guard[key])
            table.addWidget(label, row, 0)
            table.addWidget(value, row, 1)
        table.setContentsMargins(0, 5, 0, 5)
        self._layout.addLayout(table, stretch=0)
        text = QtWidgets.QTextEdit()
        text.setReadOnly(True)
        text.setText(self.guard['text'])
        text.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._layout.addWidget(text, stretch=1)
        self._layout.addStretch()
