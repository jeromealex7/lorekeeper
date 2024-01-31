from PySide2 import QtCore, QtGui, QtWidgets

from .reference_frame import ReferenceFrame
from src.model import Book, Page
from src.widgets import Icon, Text, RenameAction


class PageTab(QtWidgets.QFrame):
    DELETE = QtCore.Signal(int)
    MODIFIED = QtCore.Signal()

    def __init__(self, book: Book, page: Page, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.keep = book.keep
        self.page = page
        self.page['_book'] = book.db_index

        self.text_edit = Text(self, self.keep)
        self.text_edit.set_html(page['text'])
        self.reference_frame = ReferenceFrame(book.keep, page.db_index, self)

        layout = QtWidgets.QHBoxLayout()
        splitter = QtWidgets.QSplitter()
        layout.addWidget(splitter)
        splitter.addWidget(self.text_edit)
        splitter.addWidget(self.reference_frame)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet('QSplitter::handle {background-color: #cccccc; border: 1px solid #999999; width 0px;};')
        self.text_edit.textChanged.connect(self.MODIFIED.emit)
        self.reference_frame.REFERENCES_CHANGED.connect(self.MODIFIED.emit)
        self.setLayout(layout)

    def commit(self):
        self.page['text'] = self.text_edit.get_html()
        self.reference_frame.save_references()
        self.page.commit()

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        menu = QtWidgets.QMenu(self)
        rename_action = RenameAction(self.page, 'document_text', self)
        delete_action = QtWidgets.QAction(Icon('garbage_can'), 'Delete Page', self)
        delete_action.triggered.connect(self.on_delete)
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        menu.popup(event.globalPos())

    @property
    def db_index(self) -> int:
        return self.page.db_index

    def on_delete(self):
        self.DELETE.emit(self.page.db_index)
