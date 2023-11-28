from typing import Callable

from PySide2 import QtCore

from src.settings import SESSION


class BackgroundProcess(QtCore.QThread):
    EXCEPTION = QtCore.Signal(str, str)
    FINISHED = QtCore.Signal(tuple)

    def __init__(self, name: str = 'Unnamed Process', target: Callable[[], tuple] = None):
        super().__init__(SESSION['threadpool'])
        self.name = name
        if target:
            self.target = target

    def run(self):
        SESSION['processes'].append(self)
        try:
            result = self.target()
        except Exception as err:
            self.EXCEPTION.emit(err.__class__.__name__, str(err))
        else:
            self.FINISHED.emit(result)
        finally:
            SESSION['processes'].remove(self)
