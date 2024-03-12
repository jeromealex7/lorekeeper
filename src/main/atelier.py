from pathlib import Path
import shutil

from PySide2 import QtCore, QtGui, QtWidgets

from src.model import Keep
from src.settings import PATHS
from src.widgets import BuildingWindow, Icon


class NameEdit(QtWidgets.QLineEdit):

    def get(self) -> str:
        return self.text().strip()


class TokenEdit(QtWidgets.QPushButton):
    CHANGED = QtCore.Signal()
    IMAGE_FORMATS = ('.png', '.jpg', '.jpeg', '.webp', '.ico')
    MULTIPLE_ICONS = QtCore.Signal(tuple)

    def __init__(self, token_name: str = '', parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(50, 50)
        self.setIconSize(self.size())
        self.token_name = ''
        self.clicked.connect(self.on_click)
        self.set(token_name)

    def localize(self, file_name: str):
        if not self.token_name:
            return None
        target = PATHS['custom_tokens'].joinpath(file_name).with_suffix('.png')
        if not Path(self.token_name).exists():
            return None
        try:
            shutil.copyfile(self.token_name, target)
        except shutil.SameFileError:
            pass
        self.token_name = target.as_posix()
        return True

    def on_click(self):
        dialog = QtWidgets.QFileDialog(self, 'Select Token', Path.cwd().as_posix(),
                                       f'Images ({" ".join("*" + f for f in self.IMAGE_FORMATS)})')
        dialog.setFileMode(dialog.ExistingFiles)
        dialog.setDirectory(PATHS['media'].as_posix())
        dialog.exec_()
        files = dialog.selectedFiles()
        if not files:
            return
        self.set(files.pop(0))
        if files:
            self.MULTIPLE_ICONS.emit(files)

    def set(self, value: str):
        path = Path(value)
        self.token_name = path.as_posix()
        self.setIcon(QtGui.QIcon(self.token_name))
        self.CHANGED.emit()


class Atelier(BuildingWindow):

    def __init__(self, keep: Keep, parent: QtWidgets.QWidget | None = None, settings: dict = None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.MSWindowsFixedSizeDialogHint)
        self._is_modified = False
        self.keep = keep
        self.setWindowIcon(Icon('photo_portrait'))
        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.table.setHorizontalHeaderLabels(['Name', 'Portrait'])
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        self.table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.setFixedSize(400, 480)
        self.setCentralWidget(self.table)
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.installEventFilter(self)
        self.table.viewport().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.viewport().installEventFilter(self)
        self.set_settings(settings)

        menu_bar = QtWidgets.QMenuBar(self)
        token_menu = QtWidgets.QMenu('&Portraits', self)
        new_action = QtWidgets.QAction(Icon('photo_portrait'), 'New Portrait', self)
        new_action.triggered.connect(self.add_row)
        new_action.setShortcut(QtGui.QKeySequence('Ctrl+N'))
        save_action = QtWidgets.QAction(Icon('floppy_disk'), 'Save Portraits', self)
        save_action.triggered.connect(self.on_save)
        save_action.setShortcut(QtGui.QKeySequence('Ctrl+S'))
        close_action = QtWidgets.QAction(Icon('door_exit'), 'Close', self)
        close_action.triggered.connect(self.close)
        token_menu.addAction(new_action)
        token_menu.addAction(save_action)
        token_menu.addSeparator()
        token_menu.addAction(close_action)
        menu_bar.addMenu(token_menu)
        self.setMenuBar(menu_bar)

        self.clear_unused()
        for name in self.keep.custom_tokens:
            path = PATHS['custom_tokens'].joinpath(name).with_suffix('.png')
            if not path.exists():
                continue
            self.add_row(name, path.as_posix())

        delete_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence('Delete'), self.table)
        delete_shortcut.activated.connect(self.on_delete)
        self.reload_title()

    def add_row(self, name: str = '', token_name: str = ''):
        row = self.table.rowCount()
        self.table.setRowCount(self.table.rowCount() + 1)
        name_edit = NameEdit(name, self)
        token_edit = TokenEdit(token_name, self)
        self.table.setCellWidget(row, 0, name_edit)
        self.table.setCellWidget(row, 1, token_edit)
        name_edit.textChanged.connect(lambda _: self.set_modified(True))
        token_edit.CHANGED.connect(lambda: self.set_modified(True))
        token_edit.MULTIPLE_ICONS.connect(self.on_additional_files)
        self.table.resizeRowsToContents()
        self.table.resizeColumnToContents(1)

    def clear_unused(self):
        for path in PATHS['custom_tokens'].glob('*.png'):
            if path.stem in self.keep.custom_tokens:
                continue
            path.unlink(missing_ok=True)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if watched in (self.table.viewport(), self.table):
            if event.type() == QtCore.QEvent.ContextMenu:
                menu = QtWidgets.QMenu(self)
                new_action = QtWidgets.QAction(Icon('photo_portrait'), 'New Portrait', self)
                new_action.triggered.connect(self.add_row)
                menu.addAction(new_action)
                row = set(item.row() for item in self.table.selectedIndexes())
                if row:
                    delete_action = QtWidgets.QAction(Icon('garbage_can'), 'Remove Portrait', self)
                    delete_action.triggered.connect(self.on_delete)
                    menu.addAction(delete_action)
                menu.popup(event.globalPos())
                return True
        return super().eventFilter(watched, event)

    def get_settings(self) -> dict:
        return {'hidden': tuple(self.table.isColumnHidden(column) for column in range(self.table.columnCount()))}

    def on_additional_files(self, files: tuple[str]):
        for file_name in files:
            self.add_row(name='', token_name=file_name)

    def on_delete(self):
        selected = self.table.selectedIndexes()
        if not selected:
            return
        message_box = QtWidgets.QMessageBox(self)
        message_box.setWindowIcon(Icon('garbage_can'))
        message_box.setWindowTitle('Delete Portrait')
        message_box.setText('Delete the selected portraits?')

        def delete():
            delete_count = 0
            for row in sorted(set(item.row() for item in selected)):
                self.table.removeRow(row - delete_count)
                delete_count += 1
        delete_button = QtWidgets.QPushButton(Icon('garbage_can'), 'Delete', self)
        delete_button.clicked.connect(delete)
        cancel_button = QtWidgets.QPushButton(Icon('cancel'), 'Cancel', self)
        message_box.addButton(delete_button, message_box.AcceptRole)
        message_box.addButton(cancel_button, message_box.RejectRole)
        message_box.exec_()
        self.set_modified(True)

    def on_save(self):
        self.keep.custom_tokens = []
        deleted = 0
        for row in range(self.table.rowCount()):
            name = self.table.cellWidget(row - deleted, 0).get()
            if not name:
                self.table.removeRow(row - deleted)
                deleted += 1
                continue
            token_widget = self.table.cellWidget(row - deleted, 1)
            try:
                localize = token_widget.localize(name)
            except PermissionError:
                localize = False
            if not localize:
                continue
            self.keep.custom_tokens.append(name)
        self.keep.save_config()
        self.clear_unused()
        self.set_modified(False)

    def reload_title(self):
        title = 'Atelier - Lorekeeper'
        if self._is_modified:
            title += ' (modified)'
        self.setWindowTitle(title)

    def set_modified(self, value: bool):
        self._is_modified = value
        self.reload_title()

    def set_settings(self, settings: dict):
        if not settings:
            return
        for column, hidden in enumerate(settings.get('hidden', ())):
            self.table.setColumnHidden(column, hidden)
