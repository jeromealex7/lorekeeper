from functools import partial
import re

from PySide2 import QtGui, QtWidgets

from src.model import Guard
from .ability_highlighter import AbilityHighlighter
from .icon import Icon


class AbilityDialog(QtWidgets.QDialog):
    REGEX_BRACKET = re.compile('{(?P<name>[^:}]*?)(?::(?P<default>[^}]*?))?}')

    def __init__(self, guard: Guard, title: str, text: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._text = text
        self._title = title
        self.text = None
        self.title = None
        self.details: dict[str, str] = {}
        self.setWindowIcon(Icon('gearwheel'))
        self.setWindowTitle('Add Ability')

        self.ability_edit = QtWidgets.QTextEdit(self)
        self.ability_edit.setFont(QtGui.QFont('Roboto Slab', 10))
        self.ability_edit.setHtml(f'<i><b>{title}</b></i>\n\n{text}')
        self.ability_edit.setMinimumWidth(600)
        self.ability_edit.setReadOnly(True)
        self.highlighter = AbilityHighlighter(self.ability_edit.document(), guard.get_properties(), True)
        self.button_box = QtWidgets.QDialogButtonBox(self)
        accept_button = QtWidgets.QPushButton(Icon('ok'), 'Add Ability', self)
        accept_button.clicked.connect(self.set_data)
        cancel_button = QtWidgets.QPushButton(Icon('close'), 'Cancel', self)
        cancel_button.clicked.connect(self.deleteLater)
        self.button_box.addButton(accept_button, QtWidgets.QDialogButtonBox.AcceptRole)
        self.button_box.addButton(cancel_button, QtWidgets.QDialogButtonBox.RejectRole)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.ability_edit)
        self.detail_layout = QtWidgets.QGridLayout()
        layout.addLayout(self.detail_layout)
        layout.addWidget(self.button_box)
        for row, match in enumerate(self.REGEX_BRACKET.finditer(title + text)):
            d = match.groupdict()
            if d['name'] in self.details:
                continue
            self.details[d['name']] = d['default'] or ''
            edit = QtWidgets.QLineEdit(d['default'] or '', self)
            edit.textChanged.connect(partial(self.set_detail, d['name']))
            self.detail_layout.addWidget(QtWidgets.QLabel(d['name'] + ':'), row, 0)
            self.detail_layout.addWidget(edit, row, 1)
        self.setLayout(layout)
        if self.has_details():
            list(self.findChildren(QtWidgets.QLineEdit))[0].setFocus()

    def has_details(self) -> bool:
        return bool(self.details)

    def set_data(self):
        for match in self.REGEX_BRACKET.finditer(self._title + self._text):
            self._text = self._text.replace(match.group(), self.details[match.groupdict()['name']])
            self._title = self._title.replace(match.group(), self.details[match.groupdict()['name']])
        self.text = self._text
        self.title = self._title
        self.deleteLater()

    def set_detail(self, detail_name: str, text: str):
        self.details[detail_name] = text
