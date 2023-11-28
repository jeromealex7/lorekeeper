from PySide2 import QtCore, QtWidgets


class TextEdit(QtWidgets.QWidget):
    CHANGED = QtCore.Signal(str)

    def __init__(self, width: int = 120, text: str = '', parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.text_edit = QtWidgets.QLineEdit(self)
        size_policy = QtWidgets.QSizePolicy()
        size_policy.setVerticalPolicy(QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalPolicy(QtWidgets.QSizePolicy.Ignored)
        self.text_edit.setSizePolicy(size_policy)
        self.text_edit.setMinimumWidth(width)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

        self.text_edit.textChanged.connect(lambda _: self.CHANGED.emit(self.get()))
        self.set(text)

    def get(self) -> str:
        return self.text_edit.text().strip()

    def set(self, value: str):
        self.text_edit.setText(value.strip())
