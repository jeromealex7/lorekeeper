from PySide2 import QtWidgets

from .timer_signals import TIMER_DIAL, TIMER_STATE


class TimerDial(QtWidgets.QDial):

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.seconds = 0
        self.value_changed(0)
        self.valueChanged.connect(self.value_changed)
        self.setRange(60, 12 * 3600)
        self.setSingleStep(60)
        self.setNotchesVisible(True)
        self.setNotchTarget(1.5)

        TIMER_STATE.connect(lambda state: self.setEnabled(not state))

    def value_changed(self, new_value: int):
        self.seconds = new_value - new_value % 60
        TIMER_DIAL.emit(self.seconds)
