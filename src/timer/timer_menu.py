from PySide2 import QtCore, QtWidgets

from .timer import Timer
from .timer_dial import TimerDial
from .timer_display import TimerDisplay
from .timer_preview import TimerPreview
from src.settings import SIGNALS
from src.widgets import BuildingWindow, Icon


class TimerMenu(BuildingWindow):

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.initial_size = None
        self.frame = QtWidgets.QFrame(self)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.MSWindowsFixedSizeDialogHint)
        self.setCentralWidget(self.frame)
        self.is_reset = True
        self.setWindowIcon(Icon('horse'))
        self.setWindowTitle('Rider - Lorekeeper')

        layout = QtWidgets.QGridLayout()
        self.timer = Timer()
        self.timer_preview = TimerPreview()
        self.timer_display = TimerDisplay()
        self.timer_dial = TimerDial()
        self.play_pause_button = QtWidgets.QPushButton()
        self.stop_button = QtWidgets.QPushButton()
        self.stop_button.setIcon(Icon('media_stop'))
        self.stop_button.setText('Return Rider')
        lcd_numbers = QtWidgets.QVBoxLayout()
        lcd_numbers.addWidget(self.timer_preview)
        lcd_numbers.addWidget(self.timer_display)
        layout.addWidget(self.timer_dial, 0, 0)
        layout.addLayout(lcd_numbers, 0, 1)
        layout.addWidget(self.play_pause_button, 1, 0)
        layout.addWidget(self.stop_button, 1, 1)
        layout.setColumnMinimumWidth(0, 200)
        layout.setColumnMinimumWidth(1, 200)
        self.frame.setLayout(layout)

        self.play_pause_button.clicked.connect(self.play_pause)
        self.stop_button.clicked.connect(self.stop)
        self.update_state(False)

        SIGNALS.TIMER_STATE.connect(self.update_state)
        self.timer_dial.setValue(1800)
        SIGNALS.TIMER_DIAL.emit(self.timer_dial.seconds)
        SIGNALS.TIMER_RESET.emit(self.timer_dial.seconds)
        SIGNALS.TIMER_DIAL.connect(self.update_dial)

    def play_pause(self):
        self.is_reset = False
        SIGNALS.TIMER_STATE.emit(not self.timer.is_active)

    def stop(self):
        self.is_reset = True
        SIGNALS.TIMER_RESET.emit(self.timer_dial.seconds)

    def update_dial(self, seconds: int):
        if not self.is_reset:
            return
        SIGNALS.TIMER_RESET.emit(seconds)

    def update_state(self, active: bool):
        if active:
            self.play_pause_button.setText('Halt Rider')
            self.play_pause_button.setIcon(Icon('media_pause'))
            self.stop_button.setEnabled(False)
        else:
            self.play_pause_button.setText('Send Rider')
            self.play_pause_button.setIcon(Icon('media_play'))

            self.stop_button.setEnabled(True)
