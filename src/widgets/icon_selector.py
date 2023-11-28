from functools import partial
import math
import os
from pathlib import Path
from typing import Sequence

from PySide2 import QtCore, QtGui, QtWidgets

from .icon import Icon
from src.settings import PATHS


class IconSelector(QtWidgets.QDialog):

    def __init__(self, choices: Sequence[str | os.PathLike[str]], default: str | os.PathLike = None,
                 parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint |
                            QtCore.Qt.MSWindowsFixedSizeDialogHint)
        self.choices = [Path(choice).as_posix().__str__() for choice in choices]
        self.default = Path(default or '.')
        self.setWindowTitle('Select Icon')
        self.setWindowIcon(Icon('brush'))
        self.icon_path = None
        self.setFixedSize(self.sizeHint())

    def choose(self, icon_path: str):
        self.icon_path = icon_path
        self.deleteLater()

    def exec_(self) -> int:
        layout = QtWidgets.QGridLayout()
        layout.setSpacing(0)
        columns = math.ceil(math.sqrt(len(self.choices)))
        for index, icon_path in enumerate(self.choices):
            row = index // columns
            column = index % columns
            button = QtWidgets.QPushButton(self)
            button.setIconSize(QtCore.QSize(60, 60))
            button.setFixedSize(65, 65)
            button.setIcon(QtGui.QIcon(icon_path))
            button.clicked.connect(partial(self.choose, icon_path))
            if self.default.samefile(icon_path):
                button.setFocus()
            layout.addWidget(button, row, column)
        self.setLayout(layout)
        return super().exec_()


class BookTypeSelector(IconSelector):
    BOOK_ICONS: list[str] = ['armour', 'astrologer', 'axe', 'backpack', 'bear', 'bed_empty', 'beer_bottle',
                             'bible', 'bird', 'book', 'bottle', 'box_surprise', 'bug', 'bug2', 'bull', 'caesar',
                             'castle', 'chest_open_full', 'church', 'circus', 'cleaver', 'codes_of_law', 'cow',
                             'crossbow', 'crown', 'crystal_ball', 'dagger', 'devil', 'diamond', 'diamond_ring',
                             'dice', 'die', 'dog', 'drop', 'fortress_tower', 'gauntlet', 'ghost', 'goblet',
                             'hammer2', 'handsaw', 'helmet', 'home', 'horse', 'houses', 'key', 'leaf',
                             'location_pin', 'magic_wand', 'mail', 'map_location', 'map_location2', 'market_stand',
                             'money_coins2', 'moneybag', 'mushroom', 'pentagram', 'pirates_ship', 'poison',
                             'pontifex', 'question', 'sailboat', 'scales', 'scroll', 'scroll2', 'senior_citizen2',
                             'shield', 'skull', 'skull2', 'star2', 'store', 'sword', 'temple', 'tent', 'tree',
                             'user', 'users3', 'users_crowd', 'warehouse', 'windmill', 'wine_bottle', 'woman']

    def __init__(self,  default: str = None, parent: QtWidgets.QWidget | None = None):
        choices = [PATHS['icons'].joinpath(book_icon + '.png') for book_icon in self.BOOK_ICONS]
        super().__init__(choices=choices, default=PATHS['icons'].joinpath(default + '.png').as_posix(), parent=parent)


class TokenSelector(IconSelector):

    def __init__(self, default: str = None, parent: QtWidgets.QWidget | None = None):
        choices = [Path('.')] + list(PATHS['tokens'].glob('*.png')) + list(PATHS['custom_tokens'].glob('*.png'))
        super().__init__(choices=choices, default=default, parent=parent)
