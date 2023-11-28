import random
import re

from PySide2 import QtCore, QtWidgets

from src.widgets import Icon, RollEdit


class RollWidget(QtWidgets.QWidget):
    CHANGED = QtCore.Signal(str)
    REGEX = re.compile(r'(?P<count>[+-]?\d+)(?:d(?P<die>\d+)|\.(?P<decimals>\d{1,3}))?')
    ROLLED = QtCore.Signal(float)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.roll_edit = RollEdit(self)
        self.button = QtWidgets.QToolButton(self)
        self.button.setFixedSize(40, 40)
        self.button.setIconSize(QtCore.QSize(40, 40))
        self.button.setIcon(Icon('die'))
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.roll_edit)
        layout.addWidget(self.button)
        layout.setContentsMargins(5, 0, 5, 0)
        self.setLayout(layout)

        self.button.clicked.connect(self.roll)
        self.roll_edit.textChanged.connect(lambda: self.CHANGED.emit(self.get()))
        self.roll_edit.returnPressed.connect(self.roll)

    def get(self) -> str:
        return self.roll_edit.get()

    def roll(self) -> int:
        result = 0
        for match in self.REGEX.finditer(self.roll_edit.text().replace(' ', '')):
            group_dict = match.groupdict()
            count = int(group_dict['count'])
            decimals = group_dict['decimals'] or 0
            die = 1 if (die := group_dict['die']) is None else int(die)
            for _ in range(abs(count)):
                result += ((count > 0) - (count < 0)) * random.randint(1, die)
            result += float(f'0.{decimals}')
        if self.roll_edit.hasAcceptableInput():
            self.ROLLED.emit(result)
        return result

    def set(self, value: str | int | float):
        self.roll_edit.set(str(value))
