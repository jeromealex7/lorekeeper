from PySide2 import QtCore, QtGui, QtWidgets

from .treasure_menu import TreasureMenu
from src.model import Inscription, Treasure
from src.settings import SIGNALS, SHORTCUTS
from src.widgets import DeleteDialog, Icon, Preview, TagFrame, Text


class TreasureInspector(QtWidgets.QMainWindow):

    def __init__(self, treasure: Treasure, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet('*{font-family: Roboto Slab; font-size: 10pt;};')
        SHORTCUTS.activate_shortcuts(self)
        self._is_modified = False
        self.drag = None
        self.keep = treasure.keep
        self.treasure = treasure

        self.frame = QtWidgets.QFrame(self)
        self.text_edit = Text(self, self.keep)
        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setFixedSize(200, 200)
        self.image_label.installEventFilter(self)
        self.name_edit = QtWidgets.QLineEdit()
        self.info_edit = QtWidgets.QLineEdit()
        self.type_edit = QtWidgets.QLineEdit()
        self.suffix_edit = QtWidgets.QLineEdit()
        self.size_edit = QtWidgets.QLineEdit()
        self.uuid_edit = QtWidgets.QLineEdit()
        self.modified_edit = QtWidgets.QLineEdit()
        self.created_edit = QtWidgets.QLineEdit()
        self.info_edit.setReadOnly(True)
        self.type_edit.setReadOnly(True)
        self.suffix_edit.setReadOnly(True)
        self.size_edit.setReadOnly(True)
        self.uuid_edit.setReadOnly(True)
        self.modified_edit.setReadOnly(True)
        self.created_edit.setReadOnly(True)
        self.tag_frame = TagFrame(400, self.keep.buildings['inscription'], 'Inscription', self)

        layout = QtWidgets.QVBoxLayout()
        details = QtWidgets.QHBoxLayout()

        info = QtWidgets.QGridLayout()
        info.addWidget(QtWidgets.QLabel('Name:'), 0, 0)
        info.addWidget(QtWidgets.QLabel('Info:'), 1, 0)
        info.addWidget(QtWidgets.QLabel('Type:'), 2, 0)
        info.addWidget(QtWidgets.QLabel('Suffix:'), 3, 0)
        info.addWidget(QtWidgets.QLabel('Size:'), 4, 0)
        info.addWidget(QtWidgets.QLabel('Uuid:'), 5, 0)
        info.addWidget(QtWidgets.QLabel('Last Modified:'), 6, 0)
        info.addWidget(QtWidgets.QLabel('Created:'), 7, 0)
        info.addWidget(self.name_edit, 0, 1)
        info.addWidget(self.info_edit, 1, 1)
        info.addWidget(self.type_edit, 2, 1)
        info.addWidget(self.suffix_edit, 3, 1)
        info.addWidget(self.size_edit, 4, 1)
        info.addWidget(self.uuid_edit, 5, 1)
        info.addWidget(self.modified_edit, 6, 1)
        info.addWidget(self.created_edit, 7, 1)

        self.frame.setLayout(layout)
        self.setCentralWidget(self.frame)
        layout.addLayout(details)
        details.addLayout(info)
        details.addWidget(self.image_label)
        layout.addWidget(self.text_edit, stretch=0)
        layout.addWidget(self.tag_frame, stretch=0)
        self.load_treasure()

        menu_bar = QtWidgets.QMenuBar(self)
        file_menu = TreasureMenu(self.treasure, self, inspect=False)
        file_menu.setIcon(QtGui.QIcon())
        file_menu.setTitle('&Treasure')
        delete_action = QtWidgets.QAction(Icon('garbage_can'), 'Destroy Treasure', self)
        delete_action.triggered.connect(lambda: self.delete_treasure())
        save_action = QtWidgets.QAction(Icon('floppy_disk'), 'Save Treasure', self)
        save_action.triggered.connect(lambda: self.save())
        save_action.setShortcut(QtGui.QKeySequence('Ctrl+S'))
        reload_action = QtWidgets.QAction(Icon('refresh'), 'Reload from Treasury', self)
        reload_action.triggered.connect(lambda: self.reload_action())
        close_action = QtWidgets.QAction(Icon('door_exit'), 'Exit', self)
        close_action.triggered.connect(lambda: self.close_window())
        close_action.setShortcut(QtGui.QKeySequence('Alt+F4'))
        file_menu.addSeparator()
        file_menu.addActions([reload_action, save_action, delete_action])
        file_menu.addSeparator()
        file_menu.addAction(close_action)
        menu_bar.addMenu(file_menu)
        self.setMenuBar(menu_bar)

        self.name_edit.textChanged.connect(lambda: self.set_modified(True))
        self.text_edit.textChanged.connect(lambda: self.set_modified(True))
        self.tag_frame.TAGS_CHANGED.connect(lambda: self.set_modified(True))

        SIGNALS.TREASURE_COMMIT.connect(self.on_treasure_commit)
        SIGNALS.TREASURE_DELETE.connect(self.on_treasure_delete)

    def closeEvent(self, event: QtGui.QCloseEvent):
        self.close_window()
        event.ignore()

    def close_window(self, ask: bool = True):
        if ask and self.is_modified:
            message_box = QtWidgets.QMessageBox(self)
            message_box.setIcon(QtWidgets.QMessageBox.Warning)
            message_box.setWindowIcon(Icon('question_mark'))
            message_box.setWindowTitle('Close Window')
            message_box.setText('There are unsaved changes.')
            save_button = QtWidgets.QPushButton(Icon('floppy_disk'), 'Save and Close', self)
            close_button = QtWidgets.QPushButton(Icon('door_exit'), 'Close without saving', self)
            cancel_button = QtWidgets.QPushButton(Icon('close'), 'Cancel', self)
            message_box.addButton(save_button, QtWidgets.QMessageBox.AcceptRole)
            message_box.addButton(close_button, QtWidgets.QMessageBox.ActionRole)
            message_box.addButton(cancel_button, QtWidgets.QMessageBox.RejectRole)
            message_box.exec_()
            if message_box.clickedButton() == save_button:
                self.treasure.commit()
                self.deleteLater()
            elif message_box.clickedButton() == close_button:
                self.deleteLater()
            return
        self.deleteLater()

    def delete_inscriptions(self):
        inscription = self.treasure.keep.buildings['inscription']
        df = inscription.df
        df.drop(df[df['_treasure'] == self.treasure.db_index].index, inplace=True)
        inscription.reset_columns()
        inscription.save(False)

    def delete_treasure(self):
        if DeleteDialog('Treasure', self).get() == 'cancel':
            return
        self.treasure.delete()

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if watched == self.image_label:
            if event.type() == QtCore.QEvent.MouseButtonPress and event.buttons() == QtCore.Qt.LeftButton:
                self.on_preview_drag()
                return True
            if event.type() == QtCore.QEvent.ContextMenu:
                self.on_context_menu(event)
                return True
            if event.type() == QtCore.QEvent.MouseButtonDblClick:
                SIGNALS.IMAGE_POPUP.emit(self.treasure.db_index)
                return True
        return super().eventFilter(watched, event)

    @property
    def is_modified(self):
        return self._is_modified

    @is_modified.setter
    def is_modified(self, value):
        self._is_modified = value
        self.reload_window()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()

    def load_treasure(self):
        image = self.treasure.to_image()
        self.image_label.setPixmap(QtGui.QPixmap(image.scaled(self.image_label.size(), QtGui.Qt.KeepAspectRatio)))
        self.name_edit.setText(self.treasure['name'])
        self.info_edit.setText(self.treasure['info'])
        self.type_edit.setText(self.treasure['type'])
        self.suffix_edit.setText(self.treasure['suffix'])
        self.size_edit.setText(str(self.treasure['size'] or '- external -'))
        self.uuid_edit.setText(self.treasure['uuid'] or '- external -')
        self.modified_edit.setText(self.treasure['_modified'])
        self.created_edit.setText(self.treasure['_created'])
        self.text_edit.set_html(self.treasure['text'])
        self.tag_frame.set_tags(self.treasure.get_tags())
        self.is_modified = False

    def on_context_menu(self, event: QtCore.QEvent):
        menu = TreasureMenu(self.treasure, self, inspect=False)
        menu.popup(event.globalPos())

    def on_preview_drag(self):
        self.drag = QtGui.QDrag(self)
        self.drag.setMimeData(self.treasure.to_mime_data())
        self.drag.setPixmap(Preview(self.treasure).to_pixmap())
        self.drag.start()

    def on_treasure_commit(self, db_index: int):
        if db_index != self.treasure.db_index:
            return
        self.treasure = Treasure.read_keep(keep=self.treasure.keep, db_index=db_index)
        if self.treasure['type'] != self.type_edit.text():
            self.deleteLater()
            return
        self.reload_treasure()

    def on_treasure_delete(self, db_index: int):
        if db_index != self.treasure.db_index:
            return
        self.delete_inscriptions()
        self.deleteLater()

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
        self.load_treasure()
        self.is_modified = False

    def reload_treasure(self):
        self.name_edit.setText(self.treasure['name'])
        self.modified_edit.setText(self.treasure['_modified'])
        self.created_edit.setText(self.treasure['_created'])
        self.is_modified = False

    def reload_window(self):
        title = f'{self.name_edit.text()} - Treasury'
        if self.is_modified:
            title += ' (modified)'
        self.setWindowTitle(title)
        self.setWindowIcon(Icon(self.treasure.icon_name))

    def save(self):
        self.treasure['name'] = self.name_edit.text()
        self.treasure['text'] = self.text_edit.get_html()
        self.save_inscriptions()
        self.treasure.commit()
        self.is_modified = False

    def save_inscriptions(self):
        self.delete_inscriptions()
        keep = self.treasure.keep
        db_index = self.treasure.db_index
        for tag_name in self.tag_frame.tags:
            Inscription(keep, data={'_treasure': db_index, 'name': tag_name}).commit()
        keep.buildings['inscription'].save(False)

    def set_modified(self, modified: bool = True):
        self.is_modified = modified
