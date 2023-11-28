from PySide2 import QtWidgets

from .icon import Icon


class Error(QtWidgets.QMessageBox):

    def __init__(self, title: str = '', text: str = '', parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setText(text)
        self.setIcon(self.Critical)
        self.setWindowIcon(Icon('error'))
        self.setWindowTitle(title)
        self.ok_button = QtWidgets.QPushButton(self)
        self.ok_button.setText('Ok')
        self.addButton(self.ok_button, self.AcceptRole)

    @classmethod
    def read_exception(cls, exception: BaseException, parent: QtWidgets.QWidget | None = None):
        return cls(exception.__class__.__name__, str(exception), parent=parent)
