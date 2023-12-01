from PySide2 import QtWidgets

from .icon import Icon


class Information(QtWidgets.QMessageBox):

    def __init__(self, title: str = '', text: str = '', parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet('*{font-family: Roboto Slab; font-size: 10pt};')
        self.setText(text)
        self.setIcon(self.Information)
        self.setWindowIcon(Icon('information'))
        self.setWindowTitle(title)
        self.ok_button = QtWidgets.QPushButton(self)
        self.ok_button.setText('Ok')
        self.addButton(self.ok_button, self.AcceptRole)
