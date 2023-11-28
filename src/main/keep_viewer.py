from PySide2 import QtCore, QtGui, QtWidgets

from .keep_button_frame import KeepButtonFrame
from .keep_signals import KEEP_NEW
from src.settings import PATHS
from src.widgets import Icon


class KeepViewer(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowFlags(self.windowFlags() &
                            ~QtCore.Qt.WindowMinimizeButtonHint &
                            ~QtCore.Qt.WindowMaximizeButtonHint)
        self.setWindowTitle('Lorekeeper: Select Keep')
        self.setWindowIcon(Icon('fortress_tower'))
        self.area = QtWidgets.QScrollArea()
        self.setCentralWidget(self.area)
        self.button_frame = KeepButtonFrame(self)
        self.area.setWidget(self.button_frame)
        self.area.setWidgetResizable(True)
        self.resize(600, 600)

        menu = self.menuBar()
        new_menu = menu.addMenu('&New Keep')
        new_pathfinder = QtWidgets.QAction(QtGui.QIcon(PATHS['images'].joinpath('pathfinder').as_posix()), 'Pathfinder',
                                           self)
        new_dnd = QtWidgets.QAction(QtGui.QIcon(PATHS['images'].joinpath('dnd').as_posix()),
                                    'Dungeons and Dragons 5e', self)
        new_adnd = QtWidgets.QAction(QtGui.QIcon(PATHS['images'].joinpath('adnd').as_posix()),
                                     'Advanced Dungeons and Dragons', self)
        new_menu.addAction(new_pathfinder)
        new_menu.addAction(new_dnd)
        new_menu.addAction(new_adnd)
        new_pathfinder.triggered.connect(lambda: KEEP_NEW.emit('pathfinder'))
        new_dnd.triggered.connect(lambda: KEEP_NEW.emit('dnd'))
        new_adnd.triggered.connect(lambda: KEEP_NEW.emit('adnd'))
