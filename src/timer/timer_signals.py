from PySide2 import QtCore


class TimerSignalManager(QtCore.QObject):
    TIMER_DIAL = QtCore.Signal(int)     # seconds
    TIMER_RESET = QtCore.Signal(int)    # seconds
    TIMER_STEP = QtCore.Signal(int)     # remaining seconds
    TIMER_STATE = QtCore.Signal(bool)   # active/inactive


signal_manager = TimerSignalManager()
TIMER_DIAL = signal_manager.TIMER_DIAL
TIMER_RESET = signal_manager.TIMER_RESET
TIMER_STEP = signal_manager.TIMER_STEP
TIMER_STATE = signal_manager.TIMER_STATE
