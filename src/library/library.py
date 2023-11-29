import pandas as pd
from PySide2 import QtCore, QtGui, QtWidgets

from .book_inspector import BookInspector
from .book_table import BookTable
from .book_toolbar import BookToolbar
from src.model import Book, Keep
from src.settings import SIGNALS
from src.widgets import BuildingWindow, DeleteDialog, Icon


class Library(BuildingWindow):

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.keep = keep

        self.toolbar = BookToolbar(keep, self)
        self.book_table = BookTable(keep, self)
        self.frame = QtWidgets.QFrame(self)

        self.setWindowTitle('Library - Lorekeeper')
        self.setWindowIcon(Icon('book_open'))

        self.setCentralWidget(self.frame)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.book_table)
        self.frame.setLayout(layout)
        self.resize(1024, 768)

        self.toolbar.STATE.connect(self.book_table.toolbar_set_type)
        self.toolbar.STRING.connect(self.book_table.toolbar_set_search)
        self.book_table.SEARCH.connect(self.toolbar.search)
        SIGNALS.BOOK_INSPECT.connect(self.on_inspect_book)
        SIGNALS.BOOK_COMMIT.connect(lambda _: self.save_book())
        SIGNALS.BOOK_DELETE.connect(self.on_book_delete)
        SIGNALS.PAGE_DELETE.connect(self.on_page_delete)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        menu = QtWidgets.QMenu(self)

        def new_book():
            book = Book.new(self.keep)
            book['name'] = 'New Book'
            book['type'] = 'book'
            new_db_index = book.commit()
            SIGNALS.BOOK_INSPECT.emit(new_db_index)
        new_action = QtWidgets.QAction(Icon('plus'), 'New Book', self)
        new_action.triggered.connect(new_book)
        menu.addAction(new_action)
        if selected := self.book_table.selectedIndexes():
            db_index = self.book_table.item(selected[0].row(), 0).data(QtCore.Qt.UserRole)
            inspect_action = QtWidgets.QAction(Icon('book_open'), 'Open Book', self)
            inspect_action.triggered.connect(lambda: SIGNALS.BOOK_INSPECT.emit(db_index))
            menu.addAction(inspect_action)
            delete_action = QtWidgets.QAction(Icon('garbage_can'), 'Delete Book', self)
            delete_action.triggered.connect(lambda: self.on_delete(db_index))
            menu.addAction(delete_action)
        menu.popup(event.globalPos())

    def on_book_delete(self, db_index: int):
        for building_name in ('keyword', 'footnote'):
            building = self.keep.buildings[building_name]
            building.df.drop(building.df[building.df['_book'] == db_index].index, inplace=True)
            building.reset_columns()
            building.save(False)

        page = self.keep.buildings['page']
        page_df = page.df[page.df['_book'] == db_index]

        def delete_page(series: pd.Series):
            self.on_page_delete(int(series.name))  # noqa
        page_df.apply(delete_page, axis=1)
        page.df.drop(page_df.index, inplace=True)
        page.reset_columns()
        page.save(False)

        self.keep.buildings['book'].save(False)

    def on_delete(self, db_index: int):
        if DeleteDialog('book').get() == 'delete':
            Book.read_keep(self.keep, db_index=db_index).delete()

    def on_page_delete(self, db_index: int):
        for building_name in ('chart', 'footnote', 'sigil'):
            building = self.keep.buildings[building_name]
            df = building.df
            df.drop(df[df['_page'] == db_index].index, inplace=True)
            building.reset_columns()
            building.save(False)
        page = self.keep.buildings['page']
        page.reset_columns()
        page.save(False)

    def on_inspect_book(self, db_index: int):
        for child in QtWidgets.QApplication.topLevelWidgets():
            if not isinstance(child, BookInspector):
                continue
            if child.book.db_index == db_index:
                child.show()
                child.activateWindow()
                child.raise_()
                return
        inspector = BookInspector(Book.read_keep(self.keep, db_index=db_index))
        inspector.show()

    def save_book(self):
        self.keep.buildings['book'].save()
        self.keep.buildings['keyword'].save(False)
        self.keep.buildings['page'].save(False)
        self.keep.buildings['chart'].save(False)
        self.keep.buildings['footnote'].save(False)
        self.keep.buildings['performance'].save(False)
        self.keep.buildings['sigil'].save(False)
