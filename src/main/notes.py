from PySide2 import QtCore, QtGui, QtWidgets

from src.model import Keep
from src.widgets import Icon, Text


class Notes(QtWidgets.QTabWidget):
    CHANGED = QtCore.Signal()

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.keep = keep
        self.tabBar().setChangeCurrentOnDrag(True)
        self.setMovable(True)

    def add_page(self):
        page = Text(self, self.keep)
        self.addTab(page, 'New Page')
        page.textChanged.connect(lambda: self.CHANGED.emit())

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        menu = QtWidgets.QMenu(self)
        index = self.tabBar().tabAt(event.pos())

        def new():
            self.add_page()
            self.on_rename()
            self.tabBar().setCurrentIndex(self.tabBar().count() - 1)

        def delete():
            dialog = QtWidgets.QMessageBox(self)
            dialog.setIcon(dialog.Warning)
            dialog.setWindowTitle('Delete Page')
            dialog.setWindowIcon(Icon('garbage_can'))
            dialog.setText(f'Are you sure you want to delete page "{self.tabBar().tabText(index)}"?')
            accept_button = QtWidgets.QPushButton(Icon('garbage_can'), 'Delete', self)
            cancel_button = QtWidgets.QPushButton(Icon('cancel'), 'Cancel', self)
            dialog.addButton(accept_button, dialog.AcceptRole)
            dialog.addButton(cancel_button, dialog.RejectRole)
            accept_button.clicked.connect(lambda: (self.removeTab(index), self.CHANGED.emit()))
            dialog.exec_()
        new_action = QtWidgets.QAction(Icon('plus'), 'New Page', self)
        new_action.triggered.connect(new)
        rename_action = QtWidgets.QAction(Icon('note_text'), 'Rename Page', self)
        rename_action.triggered.connect(lambda: self.on_rename(index))
        delete_action = QtWidgets.QAction(Icon('garbage_can'), 'Delete Page', self)
        delete_action.triggered.connect(delete)
        menu.addAction(new_action)
        if index >= 0:
            self.tabBar().setCurrentIndex(index)
            menu.addAction(rename_action)
            menu.addAction(delete_action)
        menu.popup(event.globalPos())

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent):
        self.add_page()
        self.on_rename()
        self.tabBar().setCurrentIndex(self.tabBar().count() - 1)

    def get(self) -> list[tuple[str, str]]:
        return [(self.tabText(index), self.widget(index).get_html()) for index in range(self.tabBar().count())]

    def on_rename(self, index: int = None):
        if index is None:
            index = self.tabBar().count() - 1
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowIcon(Icon('note_text'))
        dialog.setWindowFlags(dialog.windowFlags() | QtCore.Qt.MSWindowsFixedSizeDialogHint)
        dialog.setWindowTitle(f'Rename Page')
        text_edit = QtWidgets.QLineEdit(self)
        text_edit.setPlaceholderText(f'Enter Page Name')
        text_edit.setText(self.tabText(index))
        text_edit.setSelection(0, len(self.tabText(index)))
        text_edit.setMinimumWidth(250)

        def rename():
            self.setTabText(index, text_edit.text())
            dialog.deleteLater()
        button_box = QtWidgets.QDialogButtonBox(self)
        accept_button = QtWidgets.QPushButton(Icon('note_text'), 'Rename', self)
        accept_button.clicked.connect(rename)
        cancel_button = QtWidgets.QPushButton(Icon('close'), 'Cancel', self)
        cancel_button.clicked.connect(dialog.deleteLater)
        button_box.addButton(accept_button, button_box.AcceptRole)
        button_box.addButton(cancel_button, button_box.RejectRole)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(text_edit)
        layout.addWidget(button_box)
        dialog.setLayout(layout)
        dialog.exec_()
        self.CHANGED.emit()

    def set(self, pages: list[tuple[str, str]]):
        while self.tabBar().count():
            self.removeTab(0)
        for index, (title, text) in enumerate(pages):
            self.add_page()
            self.widget(index).set_html(text)
            self.tabBar().setTabText(index, title)
