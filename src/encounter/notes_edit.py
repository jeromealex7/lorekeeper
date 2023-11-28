from PySide2 import QtCore, QtWidgets


class NotesEdit(QtWidgets.QWidget):
    CHANGED = QtCore.Signal()

    def __init__(self, text: str = '', parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.text_edit = QtWidgets.QPlainTextEdit(self)
        size_policy = QtWidgets.QSizePolicy()
        size_policy.setVerticalPolicy(QtWidgets.QSizePolicy.Ignored)
        size_policy.setHorizontalPolicy(QtWidgets.QSizePolicy.Preferred)
        self.text_edit.setSizePolicy(size_policy)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.text_edit.setPlainText(text)

        self.text_edit.textChanged.connect(self.CHANGED.emit)

    def get(self) -> str:
        return self.text_edit.toPlainText()

    def set(self, value: str):
        self.text_edit.setPlainText(value)