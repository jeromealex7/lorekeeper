from PySide2 import QtWidgets

from .timer_signals import TIMER_DIAL, TIMER_STATE


class TimerPreview(QtWidgets.QLCDNumber):

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(8, parent)
        TIMER_STATE.connect(self.update_state)
        TIMER_DIAL.connect(self.update_time)

    def update_state(self, new_state: bool):
        self.setEnabled(not new_state)

    def update_time(self, seconds: int):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        self.display(f'{hours:>02}:{minutes:>02}:{seconds:>02}')
