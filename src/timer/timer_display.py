from PySide2 import QtWidgets

from src.settings import SIGNALS


class TimerDisplay(QtWidgets.QLCDNumber):

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(8, parent)
        self.is_active = False
        self.seconds = 0
        self.update_state(False)
        SIGNALS.TIMER_STATE.connect(self.update_state)
        SIGNALS.TIMER_STEP.connect(self.update_time)
        SIGNALS.TIMER_RESET.connect(self.update_time)

    def update_color(self):
        if self.is_active:
            color = 'black' if self.seconds > 10 else 'red'
        else:
            color = 'gray'
        self.setStyleSheet(f'TimerDisplay{{color: {color};}};')

    def update_state(self, active: bool):
        self.is_active = active
        self.update_time(self.seconds)

    def update_time(self, seconds: int):
        self.seconds = seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        self.update_color()
        separator = ':' if seconds % 2 or not self.is_active else ' '
        self.display(f'{hours:>02}{separator}{minutes:>02}{separator}{seconds:>02}')
