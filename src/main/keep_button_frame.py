import math

from PySide2 import QtGui, QtWidgets

from .keep_button import KeepButton
from src.settings import PATHS, SIGNALS
from src.widgets import Error, Icon


class KeepButtonFrame(QtWidgets.QFrame):

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        grid = QtWidgets.QGridLayout()
        buttons = []
        for path in PATHS['keeps'].glob('*.json'):
            try:
                button = KeepButton(path)
            except Exception as err:
                Error.read_exception(err).exec_()
                continue
            buttons.append(button)
        count = len(buttons)
        columns = math.ceil(math.sqrt(count))
        for index, button in enumerate(sorted(buttons, key=lambda b: b.name)):
            row = index // columns
            column = index % columns
            grid.addWidget(button, row, column)
        self.setLayout(grid)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        menu = QtWidgets.QMenu(self)
        new_menu = QtWidgets.QMenu('New Keep', menu)
        new_pathfinder = QtWidgets.QAction(QtGui.QIcon(PATHS['images'].joinpath('pathfinder').as_posix()), 'Pathfinder',
                                           self)
        new_dnd = QtWidgets.QAction(QtGui.QIcon(PATHS['images'].joinpath('dnd').as_posix()),
                                    'Dungeons and Dragons 5e', self)
        new_adnd = QtWidgets.QAction(QtGui.QIcon(PATHS['images'].joinpath('adnd').as_posix()),
                                     'Advanced Dungeons and Dragons', self)
        new_menu.addAction(new_pathfinder)
        new_menu.addAction(new_dnd)
        new_menu.addAction(new_adnd)
        new_pathfinder.triggered.connect(lambda: SIGNALS.KEEP_NEW.emit('pathfinder'))
        new_dnd.triggered.connect(lambda: SIGNALS.KEEP_NEW.emit('dnd'))
        new_adnd.triggered.connect(lambda: SIGNALS.KEEP_NEW.emit('adnd'))
        menu.addMenu(Icon('plus'), new_menu)
