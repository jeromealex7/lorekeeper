from PySide2 import QtWidgets

from .icon import Icon


class DeleteDialog(QtWidgets.QMessageBox):

    def __init__(self, feature_name: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet('*{font-family: Roboto Slab; font-size: 10pt};')
        self.setText(f'Are you sure you want to permanently remove this {feature_name}?')
        self.setWindowTitle(f'Remove {feature_name}')
        self.setIcon(QtWidgets.QMessageBox.Warning)
        self.setWindowIcon(Icon('garbage_can'))
        self.delete_button = QtWidgets.QPushButton(Icon('garbage_can'), 'Remove', self)
        self.cancel_button = QtWidgets.QPushButton(Icon('close'), 'Cancel', self)
        self.addButton(self.delete_button, QtWidgets.QMessageBox.AcceptRole)
        self.addButton(self.cancel_button, QtWidgets.QMessageBox.RejectRole)

    def get(self) -> str:
        super().exec_()
        if self.clickedButton() == self.delete_button:
            return 'delete'
        return 'cancel'
