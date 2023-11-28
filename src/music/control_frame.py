from PySide2 import QtCore, QtGui, QtWidgets

from src.model import Keep
from src.settings import SIGNALS
from src.widgets import Icon


class ControlFrame(QtWidgets.QFrame):

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.keep = keep
        self.setStyleSheet('QFrame{border-size: 2px; border_color: black;};')
        self.now_playing = QtWidgets.QLineEdit()
        self.now_playing.setReadOnly(True)
        self.now_playing.setAlignment(QtCore.Qt.AlignCenter)
        self.now_playing.setMinimumWidth(300)
        self.now_playing.setFont(QtGui.QFont('Roboto Slab', 10))
        self.now_playing.setStyleSheet('QLineEdit{background-color: #eeeeee;};')
        self.play_pause_button = QtWidgets.QPushButton(Icon('media_stop'), 'Stop Music', self)
        self.play_pause_button.clicked.connect(self.on_stop)
        self.now_playing_label = QtWidgets.QLabel('Now Playing:')
        self.now_playing_label.setFont(QtGui.QFont('Roboto Slab', 12))
        control_layout = QtWidgets.QGridLayout()
        control_layout.addWidget(self.now_playing_label, 0, 0, QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft)
        control_layout.addWidget(self.now_playing, 1, 0)
        control_layout.addWidget(self.play_pause_button, 1, 1)
        self.setLayout(control_layout)

        SIGNALS.MUSIC_NOW_PLAYING.connect(self.on_now_playing)

    def on_now_playing(self, db_index: int):
        if db_index:
            self.now_playing.setText(self.keep.buildings['treasure'].df.at[db_index, 'name'])
        else:
            self.now_playing.setText('')

    def on_stop(self):
        SIGNALS.MUSIC_CONTINUE.emit(-2)
        self.now_playing.setText('')
