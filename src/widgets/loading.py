from typing import Callable, Sequence

from PySide2 import QtCore, QtGui, QtWidgets

from .background_process import BackgroundProcess
from .error import Error
from .icon import Icon


class Loading(QtWidgets.QDialog):

    def __init__(self, title: str, text: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint &
                            ~QtCore.Qt.WindowContextHelpButtonHint | QtCore.Qt.MSWindowsFixedSizeDialogHint)
        self.setWindowTitle(title)
        self.setWindowIcon(Icon('hourglass'))
        self.result = None
        self.resize(600, 1)
        label = QtWidgets.QLabel(text, self)
        label.resize(400, 100)
        label.setMaximumWidth(500)
        label.setWordWrap(True)
        label.setStyleSheet('QLabel{font-family: Roboto Slab; font-size: 10pt};')
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

    def closeEvent(self, event: QtGui.QCloseEvent):
        event.ignore()

    def get(self, processes: Sequence[Callable[[], tuple | None]] | Callable[[], tuple | None]) -> tuple:
        if not isinstance(processes, tuple):
            processes = (processes,)

        def target():
            return tuple(p() for p in processes)
        process = BackgroundProcess('loading', target=target)
        process.FINISHED.connect(self.on_finished)
        process.EXCEPTION.connect(self.on_exception)
        QtCore.QTimer.singleShot(100, process.start)
        self.exec_()
        return self.result

    def on_finished(self, result: tuple):
        self.result = result
        self.deleteLater()

    def on_exception(self, name: str, text: str):
        Error(title=name, text=text, parent=self).exec_()
        self.deleteLater()
