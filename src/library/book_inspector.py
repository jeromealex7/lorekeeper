import pandas as pd
from pathlib import Path
from PySide2 import QtCore, QtGui, QtWidgets

from .page_tab import PageTab
from src.model import Book, Keyword, Page, Treasure
from src.settings import SIGNALS, SHORTCUTS
from src.treasury import ImageContainer
from src.widgets import DeleteDialog, Icon, BookTypeSelector, RenameAction, RenameDialog, Summary, TagFrame


class BookInspector(QtWidgets.QMainWindow):

    def __init__(self, book: Book, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        SHORTCUTS.activate_shortcuts(self)
        self.setStyleSheet('*{font-family: Roboto Slab; font-size: 10pt;};')
        self.is_modified = False
        self.setWindowIcon(Icon('book_open'))
        self.book = book
        self.keep = book.keep
        self.db_index = book.db_index
        self.frame = QtWidgets.QFrame(self)
        self.setCentralWidget(self.frame)

        menu_bar = QtWidgets.QMenuBar(self)
        book_menu = QtWidgets.QMenu(self)
        book_menu.setTitle('&Book')
        save_action = QtWidgets.QAction(Icon('floppy_disk'), 'Save', self)
        save_action.triggered.connect(self.save)
        save_action.setShortcut(QtGui.QKeySequence('Ctrl+S'))
        reload_action = QtWidgets.QAction(Icon('refresh'), 'Reload from Library', self)
        reload_action.triggered.connect(lambda: self.reload_action())
        book_menu.addActions([save_action, reload_action])
        if self.db_index != 1:
            delete_action = QtWidgets.QAction(Icon('garbage_can'), 'Delete Book', self)
            delete_action.triggered.connect(lambda: self.on_self_delete())
            book_menu.addAction(delete_action)
        book_menu.addSeparator()
        close_action = QtWidgets.QAction(Icon('door_exit'), 'Close', self)
        close_action.triggered.connect(self.close)
        close_action.setShortcut(QtGui.QKeySequence('Alt+F4'))
        book_menu.addAction(close_action)
        self.page_menu = QtWidgets.QMenu(self)
        self.page_menu.setTitle('&Page')
        new_page_action = QtWidgets.QAction(Icon('document_text'), 'New Page', self)
        new_page_action.setShortcut(QtGui.QKeySequence('Ctrl+N'))
        new_page_action.triggered.connect(self.new_page)
        self.page_menu.addAction(new_page_action)
        menu_bar.addMenu(book_menu)
        menu_bar.addMenu(self.page_menu)
        self.setMenuBar(menu_bar)

        self.name_label = QtWidgets.QLabel('Name:', self)
        self.name_edit = QtWidgets.QLineEdit(self)
        self.type_button = QtWidgets.QPushButton(self)
        self.type_button.setIconSize(QtCore.QSize(40, 40))
        self.text_edit = Summary(self)
        self.text_edit.setFixedHeight(80)
        self.thumbnail = ImageContainer(book.keep, self)
        self.page_list = QtWidgets.QTabWidget(self)
        self.page_list.setMovable(True)
        self.page_list.setMinimumSize(200, 200)
        self.page_list.installEventFilter(self)
        self.page_list.tabBar().setChangeCurrentOnDrag(True)
        self.tag_frame = TagFrame(400, self.keep.buildings['keyword'], 'Keyword', self)

        layout = QtWidgets.QVBoxLayout()
        name_type = QtWidgets.QHBoxLayout()
        name_type.addWidget(self.name_label)
        name_type.addWidget(self.name_edit)
        name_type.addWidget(self.type_button)
        name_summary = QtWidgets.QVBoxLayout()
        name_summary.addLayout(name_type)
        name_summary.addWidget(self.text_edit)
        name_summary.addWidget(self.tag_frame, alignment=QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft, stretch=0)
        header = QtWidgets.QHBoxLayout()
        header.addLayout(name_summary, stretch=0)
        header.addWidget(self.thumbnail)
        layout.addLayout(header, stretch=0)
        layout.addWidget(self.page_list, stretch=1)
        self.frame.setLayout(layout)
        self.reload_book()

        self.name_edit.textChanged.connect(self.set_modified)
        self.text_edit.textChanged.connect(self.set_modified)
        self.tag_frame.TAGS_CHANGED.connect(lambda *_: self.set_modified(True))
        self.type_button.clicked.connect(self.on_type_button)
        self.thumbnail.TREASURE_CHANGED.connect(self.set_modified)
        SIGNALS.BOOK_COMMIT.connect(self.on_reload)
        SIGNALS.BOOK_DELETE.connect(self.on_book_delete)
        SIGNALS.TREASURE_DELETE.connect(self.on_treasure_delete)
        SIGNALS.TAB_RENAME.connect(self.on_rename)

        self.load_pages()
        self.resize(1024, 768)

    def closeEvent(self, event: QtGui.QCloseEvent):
        if self.is_modified:
            message_box = QtWidgets.QMessageBox(self)
            message_box.setWindowIcon(Icon('door_exit'))
            message_box.setWindowTitle('Close Book')
            message_box.setIcon(message_box.Warning)
            message_box.setText('There were unsaved changes.')
            save_close_button = QtWidgets.QPushButton(Icon('floppy_disk'), 'Save and Close', self)
            close_button = QtWidgets.QPushButton(Icon('door_exit'), 'Close Anyway', self)
            cancel_button = QtWidgets.QPushButton(Icon('close'), 'Cancel', self)
            message_box.addButton(save_close_button, message_box.AcceptRole)
            message_box.addButton(close_button, message_box.ActionRole)
            message_box.addButton(cancel_button, message_box.RejectRole)
            message_box.exec()
            if message_box.clickedButton() == save_close_button:
                self.save()
            elif message_box.clickedButton() == close_button:
                pass
            else:
                event.ignore()

    def delete_keywords(self):
        keyword = self.book.keep.buildings['keyword']
        df = keyword.df
        df.drop(df[df['_book'] == self.book.db_index].index, inplace=True)
        keyword.reset_columns()
        keyword.save(False)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if watched == self.page_list:
            if event.type() == QtCore.QEvent.ContextMenu:
                menu = QtWidgets.QMenu(self)
                new_page_action = QtWidgets.QAction(Icon('document_text'), 'New Page', self)
                new_page_action.triggered.connect(self.new_page)
                menu.addAction(new_page_action)
                index = self.page_list.tabBar().tabAt(event.pos())
                item = self.page_list.widget(index)
                if item:
                    rename_action = RenameAction(item.page, 'document_text', self)
                    menu.addAction(rename_action)
                    self.page_list.tabBar().setCurrentIndex(index)
                    delete_action = QtWidgets.QAction(Icon('garbage_can'), 'Delete Page', self)
                    delete_action.triggered.connect(lambda: self.on_delete(index))
                    menu.addAction(delete_action)
                menu.popup(event.globalPos())
                return True
            if event.type() == QtCore.QEvent.MouseButtonDblClick:
                self.new_page()
                return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()

    def load_pages(self):
        df = self.keep.buildings['page'].df
        df = df[df['_book'] == self.db_index].sort_values(by='list_index')

        def _new_page(series: pd.Series):
            page = Page.read_keep(self.keep, int(series.name))  # noqa
            tab = PageTab(self.book, page)
            tab.MODIFIED.connect(self.set_modified)
            tab.DELETE.connect(self.on_tab_delete)
            self.page_list.addTab(tab, page['name'])
        df.apply(_new_page, axis=1)

    def new_page(self):
        page = Page.new(self.keep)
        page['name'] = 'New Page'
        page.commit()
        tab = PageTab(self.book, page)
        self.page_list.addTab(tab, page['name'])
        tab.MODIFIED.connect(self.set_modified)
        tab.DELETE.connect(self.on_tab_delete)
        RenameDialog(page, 'document_text', self).exec_()
        self.set_modified(True)
        self.page_list.setCurrentIndex(self.page_list.count() - 1)

    def on_book_delete(self, db_index: int):
        if self.db_index != db_index:
            return
        self.deleteLater()

    def on_delete(self, index: int):
        if DeleteDialog('page').get() == 'delete':
            self.page_list.widget(index).page.delete()
            self.page_list.removeTab(index)
            self.set_modified(True)

    def on_self_delete(self):
        if DeleteDialog('book').get() == 'delete':
            self.book.delete()

    def on_tab_delete(self, db_index: int):
        for row in range(self.page_list.count()):
            tab = self.page_list.widget(row)
            if tab.db_index != db_index:
                continue
            self.on_delete(row)
            break

    def on_reload(self, db_index: int):
        if db_index != self.db_index:
            return
        self.reload_book()

    def on_rename(self, table_name: str, db_index: int, name: str):
        if table_name != 'page':
            return
        for row in range(self.page_list.count()):
            tab = self.page_list.widget(row)
            if tab.db_index != db_index:
                continue
            self.page_list.setTabText(row, name)
        self.set_modified(True)

    def on_treasure_delete(self, db_index: int):
        if db_index != self.book['_treasure']:
            return
        self.book['_treasure'] = 0
        self.thumbnail.set_content(None)

    def on_type_button(self):
        icon_selector = BookTypeSelector(default=self.book['type'], parent=self)
        icon_selector.exec_()
        if not icon_selector.icon_path:
            return
        self.set_modified(True)
        self.book['type'] = Path(icon_selector.icon_path).stem
        self.type_button.setIcon(Icon(self.book['type']))
        self.reload_title()

    def reload_action(self):
        if self.is_modified:
            message_box = QtWidgets.QMessageBox(self)
            message_box.setWindowIcon(Icon('refresh'))
            message_box.setIcon(QtWidgets.QMessageBox.Warning)
            message_box.setWindowTitle('Reload Treasure')
            message_box.setText('There were unsaved changes.')
            refresh_button = QtWidgets.QPushButton(Icon('refresh'), 'Reload Anyway', self)
            cancel_button = QtWidgets.QPushButton(Icon('close'), 'Cancel', self)
            message_box.addButton(refresh_button, QtWidgets.QMessageBox.AcceptRole)
            message_box.addButton(cancel_button, QtWidgets.QMessageBox.RejectRole)
            message_box.exec_()
            if message_box.clickedButton() == cancel_button:
                return
        self.reload_book()
        self.set_modified(False)

    def reload_book(self):
        self.book = Book.read_keep(self.keep, self.db_index)
        self.name_edit.setText(self.book['name'])
        self.text_edit.setPlainText(self.book['text'])
        self.type_button.setIcon(Icon(self.book['type']))
        self.tag_frame.set_tags(self.book.get_tags())
        try:
            treasure = Treasure.read_keep(self.keep, int(self.book['_treasure']))
        except KeyError:
            treasure = None
        self.thumbnail.set_content(treasure)
        self.reload_title()
        self.set_modified(False)

    def reload_title(self):
        title = self.name_edit.text()
        if self.is_modified:
            title += ' (modified)'
        self.setWindowIcon(self.type_button.icon())
        self.setWindowTitle(title)

    def save(self):
        self.book['name'] = self.name_edit.text()
        self.book['text'] = self.text_edit.toPlainText()
        db_index = treasure.db_index or treasure.commit() if (treasure := self.thumbnail.treasure) else 0
        self.book['_treasure'] = db_index
        self.save_keywords()
        self.save_pages()
        self.book.commit()

    def save_keywords(self):
        self.delete_keywords()
        keep = self.book.keep
        db_index = self.book.db_index
        for tag_name in self.tag_frame.tags:
            Keyword(keep, data={'_book': db_index, 'name': tag_name}).commit()
        keep.buildings['keyword'].save(False)

    def save_pages(self):
        for row in range(self.page_list.tabBar().count()):
            tab = self.page_list.widget(row)
            tab.page['list_index'] = row
            tab.page['name'] = self.page_list.tabText(row)
            tab.commit()

    def set_modified(self, state: bool = True):
        self.is_modified = state
        self.reload_title()
