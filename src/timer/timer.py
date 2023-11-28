from typing import Literal

from PySide2 import QtCore, QtWidgets

from .timer_signals import TIMER_RESET, TIMER_STEP, TIMER_STATE
from src.widgets import Icon


class Timer(QtCore.QTimer):

    def __init__(self):
        super().__init__()
        self.is_active = False
        self.remaining_time = 0
        self.starting_time = 0

        self.timeout.connect(self.step_seconds)
        self.start(1000)
        TIMER_STATE.connect(self.set_state)
        TIMER_RESET.connect(self.timer_reset)

    def execute(self):
        message_box = QtWidgets.QMessageBox()
        message_box.setWindowTitle('Rider Arrived')
        message_box.setText('The Rider has arrived!')
        message_box.setIcon(QtWidgets.QMessageBox.Information)
        message_box.setWindowIcon(Icon('horse'))
        button_restart = QtWidgets.QPushButton(Icon('horse'), 'Resend Rider', self.parent())
        button_nothing = QtWidgets.QPushButton(Icon('ok'), 'Ok', self.parent())
        message_box.addButton(button_restart, QtWidgets.QMessageBox.AcceptRole)
        message_box.addButton(button_nothing, QtWidgets.QMessageBox.RejectRole)
        message_box.exec_()
        if message_box.clickedButton() == button_restart:
            TIMER_RESET.emit(self.starting_time)
            TIMER_STATE.emit(True)

    def set_state(self, new_state: bool | Literal['toggle'] = True):
        self.is_active = (not self.is_active) if new_state == 'toggle' else new_state

    def step_seconds(self):
        if not self.is_active:
            return
        self.remaining_time -= 1
        if self.remaining_time >= 0:
            TIMER_STEP.emit(self.remaining_time)
            if not self.remaining_time:
                TIMER_STATE.emit(False)
                self.execute()
        else:
            self.remaining_time = self.starting_time

    def timer_reset(self, seconds: int):
        self.remaining_time = seconds
        self.starting_time = seconds
