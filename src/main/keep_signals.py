from PySide2 import QtCore


class KeepSignalManager(QtCore.QObject):
    KEEP_OPEN = QtCore.Signal(str)  # uuid
    KEEP_NEW = QtCore.Signal(str)   # ruleset


signal_manager = KeepSignalManager()
KEEP_OPEN = signal_manager.KEEP_OPEN
KEEP_NEW = signal_manager.KEEP_NEW
